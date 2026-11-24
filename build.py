#!/usr/bin/env python3
"""Build Graft and Graft Mono.

Graft is an interpolation between two typefaces: Geist and Public Sans for
the sans, Geist Mono and JetBrains Mono for the mono. Every letter both fonts
share is made point-compatible (see blend.py) and drawn at a mix ratio, so
proportions, x-height, curves and terminals all land between the two designs.

The second font is weight-matched to Geist at each of Geist's masters by
measuring stems, so the result is one variable font whose 100-900 weights
mean what they say. Geist supplies the spacing tables, OpenType features and
any glyph the second font cannot be matched against.

Usage: python build.py
"""

from __future__ import annotations

import copy
import sys
import unicodedata
from pathlib import Path

from fontTools.designspaceLib import AxisDescriptor, DesignSpaceDocument, SourceDescriptor
from fontTools.pens.basePen import BasePen
from fontTools.pens.recordingPen import DecomposingRecordingPen, RecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.varLib import build as build_variable_font
from fontTools.varLib import instancer

import blend

ROOT = Path(__file__).resolve().parent
VERSION = "0.2.000"

# `mix` is the design: 0 is pure Geist, 1 is pure second font. A letter the
# two fonts build differently can't be blended; it takes the drawing of the
# font the mix leans toward.
FAMILIES = {
    "sans": {
        "base": "sources/Geist[wght].ttf",
        "donor": "sources/PublicSans[wght].ttf",
        "family": "Graft",
        "psFamily": "Graft",
        "basePsFamily": "Geist",
        "mono": False,
        "mix": 0.55,
        "output": "fonts/Graft[wght]",
    },
    "mono": {
        "base": "sources/GeistMono[wght].ttf",
        "donor": "sources/JetBrainsMono[wght].ttf",
        "family": "Graft Mono",
        "psFamily": "GraftMono",
        "basePsFamily": "GeistMono",
        "mono": True,
        "mix": 0.45,
        # Glyphs that keep Geist's drawing whatever the mix: Geist Mono's
        # slashed zero reads better in code than JetBrains Mono's dotted one.
        "keep": ("zero",),
        # Characters drawn with the second font's design whatever the mix, in
        # every form both fonts draw (numerators, denominators). Their two
        # designs differ in structure, so there is no blend between them, and
        # these are the shapes that make the mono read as its own face.
        "take": ("r", "l", "6", "9"),
        "output": "fonts/GraftMono[wght]",
    },
}

# Marks and modifier letters keep Geist's drawings so composite offsets stay valid.
# A blend whose ink area strays further than this from the sources' mean is
# averaging two different structures; Geist's drawing is kept instead.
AREA_TOLERANCE = 0.03
# Small marks (a period, a quote) can drift a few percent just from a round
# dot meeting a square one; ignore drifts under this fraction of an em square.
AREA_FLOOR = 0.0015

SKIP_CATEGORIES = {"Mn", "Me", "Sk", "Lm", "Cc", "Cf", "Zs"}


class BuildError(Exception):
    pass


# --- measuring -------------------------------------------------------------


class FlattenPen(BasePen):
    """Records outlines as line segments so stems can be measured with a ray."""

    def __init__(self, glyphSet=None, steps: int = 24):
        super().__init__(glyphSet)
        self.steps = steps
        self.segments: list[tuple[tuple[float, float], tuple[float, float]]] = []
        self._start = self._last = None

    def _moveTo(self, pt):
        self._start = self._last = pt

    def _lineTo(self, pt):
        self.segments.append((self._last, pt))
        self._last = pt

    def _curveToOne(self, p1, p2, p3):
        p0 = self._last
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            x = mt**3 * p0[0] + 3 * mt**2 * t * p1[0] + 3 * mt * t**2 * p2[0] + t**3 * p3[0]
            y = mt**3 * p0[1] + 3 * mt**2 * t * p1[1] + 3 * mt * t**2 * p2[1] + t**3 * p3[1]
            self._lineTo((x, y))

    def _qCurveToOne(self, p1, p2):
        p0 = self._last
        for i in range(1, self.steps + 1):
            t = i / self.steps
            mt = 1 - t
            x = mt * mt * p0[0] + 2 * mt * t * p1[0] + t * t * p2[0]
            y = mt * mt * p0[1] + 2 * mt * t * p1[1] + t * t * p2[1]
            self._lineTo((x, y))

    def _closePath(self):
        if self._last != self._start:
            self._lineTo(self._start)

    _endPath = _closePath


def glyph_bounds(glyph_set, name):
    pen = FlattenPen(glyph_set)
    glyph_set[name].draw(pen)
    xs = [p[0] for seg in pen.segments for p in seg]
    ys = [p[1] for seg in pen.segments for p in seg]
    return min(xs), min(ys), max(xs), max(ys)


def left_stem(glyph_set, name, y):
    """Width of the first stem crossed by a horizontal ray at height y."""
    pen = FlattenPen(glyph_set)
    glyph_set[name].draw(pen)
    xs = sorted(
        a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
        for a, b in pen.segments
        if (a[1] - y) * (b[1] - y) < 0
    )
    if len(xs) < 2:
        raise BuildError(f"Could not measure a stem in `{name}` at y={y:.1f}.")
    return xs[1] - xs[0]


class _Recorded:
    def __init__(self, rec):
        self.rec = rec

    def draw(self, pen):
        self.rec.replay(pen)


def glyph_name(font, char):
    name = font.getBestCmap().get(ord(char))
    if name is None:
        raise BuildError(f"`{char}` (U+{ord(char):04X}) is missing from {font.reader.file.name}.")
    return name


def group_of(char):
    return "lc" if char.islower() else "uc"


# --- weight matching -------------------------------------------------------


def base_master_weights(base):
    """User-space weights where the base font has masters, read from gvar."""
    if "avar" in base:
        raise BuildError("The base font has an `avar` table; master recovery assumes it has none.")
    (axis,) = [a for a in base["fvar"].axes if a.axisTag == "wght"]
    peaks = {0.0}
    for variations in base["gvar"].variations.values():
        for var in variations:
            peaks.add(var.axes["wght"][1])
    weights = []
    for p in sorted(peaks):
        span = axis.maxValue - axis.defaultValue if p > 0 else axis.defaultValue - axis.minValue
        weights.append(axis.defaultValue + p * span)
    return weights


def match_donor_weight(donor, donor_axis, measure, target):
    """Bisect the donor weight whose scaled stem equals the target stem."""
    lo, hi = donor_axis.minValue, donor_axis.maxValue
    f_lo, f_hi = measure(lo), measure(hi)
    if target <= f_lo:
        return lo, f_lo
    if target >= f_hi:
        return hi, f_hi
    for _ in range(40):
        mid = (lo + hi) / 2
        if measure(mid) < target:
            lo = mid
        else:
            hi = mid
    w = (lo + hi) / 2
    return w, measure(w)


# --- grafting --------------------------------------------------------------


def offset_outline(glyph, sigma, height):
    """Grow (sigma > 0) or shrink every stroke by sigma units per side.

    Each point moves along the bisector of its neighbouring edge normals, the
    way FreeType emboldens, so the point structure (and therefore variation
    compatibility) is unchanged. The result is then refit vertically so the
    baseline and the x-height or cap height stay where they were.
    """
    coords = [tuple(map(float, c)) for c in glyph.coordinates]
    if not coords or not sigma:
        return
    start = 0
    area = 0.0
    contours = []
    for end in glyph.endPtsOfContours:
        pts = coords[start : end + 1]
        contours.append((start, pts))
        area += sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1]))
        start = end + 1
    # TrueType outlines run clockwise (negative area), so the left normal of
    # each edge points out of the ink. Flip it for counter-clockwise fonts.
    side = 1.0 if area < 0 else -1.0

    def normal(a, b):
        dx, dy = b[0] - a[0], b[1] - a[1]
        length = (dx * dx + dy * dy) ** 0.5
        return (-dy / length * side, dx / length * side) if length else None

    out = list(coords)
    for start, pts in contours:
        n = len(pts)
        for i, p in enumerate(pts):
            prev = next((pts[(i - k) % n] for k in range(1, n) if pts[(i - k) % n] != p), None)
            nxt = next((pts[(i + k) % n] for k in range(1, n) if pts[(i + k) % n] != p), None)
            if prev is None or nxt is None:
                continue
            n1, n2 = normal(prev, p), normal(p, nxt)
            denom = max(1 + n1[0] * n2[0] + n1[1] * n2[1], 0.35)
            out[start + i] = (
                p[0] + (n1[0] + n2[0]) * sigma / denom,
                p[1] + (n1[1] + n2[1]) * sigma / denom,
            )
    k = height / (height + 2 * sigma)
    glyph.coordinates = type(glyph.coordinates)([(round(x), round((y + sigma) * k)) for x, y in out])


def draw_donor_glyph(donor_set, donor_name, scale, cell_width, sigma=0.0, height=0.0):
    rec = DecomposingRecordingPen(donor_set)
    donor_set[donor_name].draw(rec)
    pen = TTGlyphPen(None)
    rec.replay(TransformPen(pen, (scale, 0, 0, scale, 0, 0)))
    glyph = pen.glyph()
    offset_outline(glyph, sigma, height)
    # Sidebearings follow the stroke change so spacing stays even.
    width = donor_set[donor_name].width * scale + 2 * sigma
    if cell_width is None:
        advance, dx = round(width), sigma
    else:
        advance, dx = cell_width, (cell_width - width) / 2 + sigma
    if glyph.numberOfContours > 0:
        glyph.coordinates.translate((round(dx), 0))
    return glyph, advance


def glyph_edges(glyph_set, name, depth=0.12):
    """Edge centers and vertical extent of a glyph's ink, or None if empty."""
    pen = FlattenPen(glyph_set)
    glyph_set[name].draw(pen)
    pts = [p for seg in pen.segments for p in seg]
    if not pts:
        return None
    y0 = min(p[1] for p in pts)
    y1 = max(p[1] for p in pts)
    band = (y1 - y0) * depth

    def center(keep):
        xs = [p[0] for p in pts if keep(p[1])]
        return (min(xs) + max(xs)) / 2

    return {
        "top": center(lambda y: y >= y1 - band),
        "bottom": center(lambda y: y <= y0 + band),
        "yMax": y1,
        "yMin": y0,
        "middle": (y0 + y1) / 2,
    }


def repair_composites(master, changed, old_edges, old_advance, mark_names):
    """Keep composites in step with the blended glyphs they are built from.

    Spacing components after a resized one move by its width change (ǆ, Ĳ).
    Marks follow the top or bottom edge of the letter they sit on (á, ç).
    """
    glyf, hmtx = master["glyf"], master["hmtx"]
    changed = set(changed)
    repaired = set()
    pending = True
    while pending:
        pending = False
        glyph_set = master.getGlyphSet()
        new_edges = {n: glyph_edges(glyph_set, n) for n in changed if n not in repaired}
        for name in master.getGlyphOrder():
            g = glyf[name]
            if name in changed or not g.isComposite():
                continue
            if not any(c.glyphName in changed for c in g.components):
                continue
            shift, carrier = 0, None
            for comp in g.components:
                cname = comp.glyphName
                if cname in mark_names:
                    if carrier is None or carrier[0] not in changed:
                        comp.x += round(carrier[1]) if carrier else 0
                        continue
                    base_name, base_shift = carrier
                    old, new = old_edges[base_name], new_edges.get(base_name) or glyph_edges(glyph_set, base_name)
                    if old is None or new is None:
                        continue
                    mark = glyf[cname]
                    mark.recalcBounds(glyf)
                    above = (mark.yMin + mark.yMax) / 2 + comp.y > old["middle"]
                    if above:
                        comp.x += round(new["top"] - old["top"] + base_shift)
                        comp.y += round(new["yMax"] - old["yMax"])
                    else:
                        comp.x += round(new["bottom"] - old["bottom"] + base_shift)
                        comp.y += round(new["yMin"] - old["yMin"])
                else:
                    comp.x += round(shift)
                    carrier = (cname, shift)
                    shift += hmtx[cname][0] - old_advance[cname]
            g.recalcBounds(glyf)
            hmtx[name] = (old_advance[name] + round(shift), g.xMin if hasattr(g, "xMin") else 0)
            changed.add(name)
            repaired.update(new_edges)
            pending = True
    return changed


# Figure variants that both fonts reach through the same OpenType feature.
# Blending them keeps tabular, superscript and fraction figures in the same
# style as the default digits.
FIGURE_FEATURES = ("tnum", "pnum", "sups", "subs", "sinf", "numr", "dnom")


def single_substitutions(font, tag):
    """Glyph-to-glyph substitutions a GSUB feature makes."""
    if "GSUB" not in font:
        return {}
    table = font["GSUB"].table
    mapping = {}
    for record in table.FeatureList.FeatureRecord:
        if record.FeatureTag != tag:
            continue
        for index in record.Feature.LookupListIndex:
            lookup = table.LookupList.Lookup[index]
            for sub in lookup.SubTable:
                if lookup.LookupType == 7:
                    sub = sub.ExtSubTable
                mapping.update(getattr(sub, "mapping", None) or {})
    return mapping


def enforce_tabular(master, names, width):
    """Give every tabular figure one advance and center its ink, so columns
    of numbers line up after blending changed the digits' widths."""
    glyf, hmtx = master["glyf"], master["hmtx"]
    glyph_set = master.getGlyphSet()
    for name in names:
        x0, _, x1, _ = glyph_bounds(glyph_set, name)
        dx = round((width - (x1 - x0)) / 2 - x0)
        g = glyf[name]
        if g.isComposite():
            for comp in g.components:
                comp.x += dx
        else:
            g.coordinates.translate((dx, 0))
        g.recalcBounds(glyf)
        hmtx[name] = (width, g.xMin)


def candidates(base, donor):
    """Glyphs both fonts draw for the same character, with their groups."""
    out = {}
    donor_cmap = donor.getBestCmap()
    mapped = []
    for code, name in sorted(base.getBestCmap().items()):
        if name in out or code not in donor_cmap:
            continue
        char = chr(code)
        if unicodedata.category(char) in SKIP_CATEGORIES:
            continue
        mapped.append((name, donor_cmap[code], char))
        if base["glyf"][name].isComposite():
            continue
        out[name] = (donor_cmap[code], group_of(char), char)
    for tag in FIGURE_FEATURES:
        base_subs, donor_subs = single_substitutions(base, tag), single_substitutions(donor, tag)
        for name, dname, char in mapped:
            variant, donor_variant = base_subs.get(name), donor_subs.get(dname)
            if not variant or not donor_variant or variant in out:
                continue
            if base["glyf"][variant].numberOfContours <= 0:
                continue
            out[variant] = (donor_variant, group_of(char), char)
    return out


def rename(vf, base, donor, cfg):
    family, ps = cfg["family"], cfg["psFamily"]
    name = base["name"].__class__()
    name.names = []
    donor_names = donor["name"]
    base_names = base["name"]

    def get(table, nid):
        rec = table.getName(nid, 3, 1, 0x409)
        return rec.toUnicode() if rec else ""

    keep = {}
    for rec in base_names.names:
        if rec.platformID == 3 and rec.nameID >= 256:
            keep[rec.nameID] = rec.toUnicode().replace(cfg["basePsFamily"] + "-", ps + "-")
    records = {
        0: f"{get(base_names, 0)}. {get(donor_names, 0)}. Graft modifications Copyright 2026 Farming Labs.",
        1: family,
        2: "Regular",
        3: f"{VERSION};FRML;{ps}-Regular",
        4: f"{family} Regular",
        5: f"Version {VERSION}",
        6: f"{ps}-Regular",
        8: "Farming Labs",
        9: f"Geist: {get(base_names, 9)}. {get(donor_names, 9)}",
        13: get(base_names, 13),
        14: get(base_names, 14),
        25: ps,
        **keep,
    }
    for nid, text in records.items():
        name.setName(text, nid, 3, 1, 0x409)
    vf["name"] = name
    vf["head"].fontRevision = float(VERSION.split(".")[0] + "." + VERSION.split(".")[1])

    leaked = [
        (r.nameID, r.toUnicode())
        for r in name.names
        if r.nameID not in (0, 9, 13) and ("Geist" in r.toUnicode() or "Basement" in r.toUnicode())
    ]
    if leaked:
        raise BuildError(f"Base font names leaked into {family}: {leaked}")


# --- build -----------------------------------------------------------------


def build_family(key, cfg):
    base = TTFont(ROOT / cfg["base"])
    donor = TTFont(ROOT / cfg["donor"])
    mix = cfg["mix"]
    (base_axis,) = base["fvar"].axes
    (donor_axis,) = donor["fvar"].axes
    scale = base["head"].unitsPerEm / donor["head"].unitsPerEm
    em = base["head"].unitsPerEm
    donor_default = donor.getGlyphSet()
    probe = {"lc": ("n", "x", 0.35), "uc": ("H", "H", 0.25)}

    def height(gs, font, char):
        return glyph_bounds(gs, glyph_name(font, char))[3]

    masters = base_master_weights(base)
    default_index = masters.index(base_axis.defaultValue)
    print(f"[{key}] masters at wght {', '.join(f'{w:g}' for w in masters)}; mix {mix:g}")

    cell = base["hmtx"][glyph_name(base, "n")][0] if cfg["mono"] else None
    todo = candidates(base, donor)
    statics, outlines, report = [], [], []
    for w in masters:
        master = instancer.instantiateVariableFont(base, {"wght": w}, inplace=False)
        master_set = master.getGlyphSet()
        donor_sets, corrections = {}, {}
        for group, (char, h_char, frac) in probe.items():
            h = height(master_set, master, h_char)
            target = left_stem(master_set, glyph_name(master, char), h * frac + 0.5)
            d_h = height(donor_default, donor, h_char)

            def measure(dw, char=char, frac=frac, d_h=d_h):
                gs = donor.getGlyphSet(location={"wght": dw})
                return left_stem(gs, glyph_name(donor, char), d_h * frac + 0.5) * scale

            dw, got = match_donor_weight(donor, donor_axis, measure, target)
            sigma = (target - got) / 2 if abs(target - got) > 1 else 0.0
            donor_sets[group] = donor.getGlyphSet(location={"wght": dw})
            corrections[group] = (sigma, d_h * scale)
            report.append((w, group, target, dw, got, sigma))

        per_glyph = {}
        for name, (dname, group, _) in todo.items():
            sigma, h = corrections[group]
            dglyph, dadv = draw_donor_glyph(donor_sets[group], dname, scale, cell, sigma, h)
            draw_a = master_set[name].draw
            draw_b = lambda pen, g=dglyph: g.draw(pen, None)  # noqa: E731
            a, b = blend.segments_of(draw_a), blend.segments_of(draw_b)
            # One font may draw a letter with overlapping strokes (Geist's f is a
            # stem plus a crossbar, Geist Mono's A is legs plus a bar); the
            # second attempt blends those outlines unioned into single shapes.
            merged = (blend.segments_of(blend.merged(draw_a)), blend.segments_of(blend.merged(draw_b)))
            per_glyph[name] = (a, b, master["hmtx"][name][0], dadv, merged, dglyph)
        statics.append(master)
        outlines.append(per_glyph)

    for w, group, target, dw, got, sigma in report:
        print(
            f"[{key}] wght {w:7.2f} {group}: Geist stem {target:6.1f} -> second font wght {dw:6.1f} "
            f"({got:6.1f}), offset {sigma:+5.1f}"
        )

    def try_blend(sources):
        """Blend one glyph from per-master (a, b) outlines, or raise Incompatible."""
        a0, b0 = sources[default_index]
        plan = blend.plan_glyph(a0, b0, em)
        per_master = [blend.blend_contours(plan, a, b, mix) for a, b in sources]
        plan_b = [step["b"] for step in plan]
        for (a, b), mixed in zip(sources, per_master):
            # A blend that crosses itself where neither source does means the
            # outlines were matched wrongly.
            a_x, b_x = blend.source_crossings(a), blend.source_crossings(b)
            for ci, crossings in enumerate(blend.self_crossings(mixed)):
                if crossings and not a_x[ci] and not b_x[plan_b[ci]]:
                    raise blend.Incompatible("blended outline crosses itself")
            ratio, drift = blend.area_ratio(mixed, a, b, mix)
            if abs(ratio - 1) > AREA_TOLERANCE and drift > AREA_FLOOR * em * em:
                raise blend.Incompatible(f"the two designs differ in structure (ink {ratio - 1:+.1%})")
        pens = [TTGlyphPen(None) for _ in sources]
        blend.draw_compatible(pens, per_master)
        return [pen.glyph() for pen in pens]

    blended, kept, swapped = {}, {}, {}
    for name in todo:
        if name in cfg.get("keep", ()):
            kept[name] = "kept by choice"
            continue
        if todo[name][2] in cfg.get("take", ()):
            glyphs = [copy.deepcopy(o[name][5]) for o in outlines]
            if len({(len(g.coordinates), tuple(g.endPtsOfContours), bytes(g.flags)) for g in glyphs}) != 1:
                raise BuildError(f"`{name}` from the second font changes point structure across masters.")
            blended[name] = glyphs
            swapped[name] = "taken by choice"
            continue
        a0, b0 = outlines[default_index][name][:2]
        if not a0 and not b0:
            blended[name] = None  # Empty glyph such as a space: blend the advance only.
            continue
        attempts = [[o[name][:2] for o in outlines]]
        reasons = []
        # Union only the side whose strokes overlap, decided at the default
        # master so every master takes the same outline.
        # Unioned outlines interpolate as they are when pathops happens to give
        # every master the same structure.
        merged = [o[name][4] for o in outlines]
        if blend.same_structure([m[0] for m in merged]) and blend.same_structure([m[1] for m in merged]):
            attempts.append(merged)
        # Otherwise the union is planned once and rebuilt at every master, so
        # the outline keeps one point structure across the weight axis.
        union_a, union_b = outlines[default_index][name][4]
        try:
            plan_a = blend.union_plan(a0, union_a) if blend.overlaps(a0, union_a) else None
            plan_b = blend.union_plan(b0, union_b) if blend.overlaps(b0, union_b) else None
            if plan_a or plan_b:
                attempts.append(
                    [
                        (
                            blend.apply_union(plan_a, o[name][0]) if plan_a else o[name][0],
                            blend.apply_union(plan_b, o[name][1]) if plan_b else o[name][1],
                        )
                        for o in outlines
                    ]
                )
        except blend.Incompatible as error:
            reasons.append(str(error))
        for sources in attempts:
            try:
                glyphs = try_blend(sources)
                break
            except blend.Incompatible as error:
                reasons.append(str(error))
        else:
            if mix <= 0.5:
                kept[name] = "; ".join(reasons)
                continue
            # The mix leans to the second font: use its drawing, already
            # weight-matched and scaled for each master.
            glyphs = [copy.deepcopy(o[name][5]) for o in outlines]
            swapped[name] = "; ".join(reasons)
        shapes = {(len(g.coordinates), tuple(g.endPtsOfContours), bytes(g.flags)) for g in glyphs}
        if len(shapes) != 1:
            raise BuildError(f"`{name}` blended to different point structures across masters.")
        blended[name] = glyphs

    gdef = base["GDEF"].table.GlyphClassDef.classDefs if "GDEF" in base else {}
    mark_names = {n for n, c in gdef.items() if c == 3} | {
        n for n in base.getGlyphOrder() if base["hmtx"][n][0] == 0 and base["glyf"][n].numberOfContours
    }

    tabular = {v for k, v in single_substitutions(base, "tnum").items() if base["glyf"][v].numberOfContours}

    ds = DesignSpaceDocument()
    ds.addAxis(
        AxisDescriptor(
            tag="wght",
            name="Weight",
            minimum=base_axis.minValue,
            default=base_axis.defaultValue,
            maximum=base_axis.maxValue,
        )
    )
    for i, (w, master) in enumerate(zip(masters, statics)):
        glyf, hmtx = master["glyf"], master["hmtx"]
        old_set = master.getGlyphSet()
        old_edges = {n: glyph_edges(old_set, n) for n in master.getGlyphOrder() if glyf[n].numberOfContours}
        old_advance = {n: hmtx[n][0] for n in master.getGlyphOrder()}
        for name, glyphs in blended.items():
            _, _, a_adv, b_adv, _, _ = outlines[i][name]
            if cell:
                advance = cell
            elif name in swapped:
                advance = b_adv
            else:
                advance = round(a_adv + (b_adv - a_adv) * mix)
            if glyphs is None:
                hmtx[name] = (advance, 0)
                continue
            glyph = glyphs[i]
            glyph.recalcBounds(glyf)
            glyf[name] = glyph
            hmtx[name] = (advance, glyph.xMin)
        repair_composites(master, blended, old_edges, old_advance, mark_names)
        if tabular:
            blended_tabular = [n for n in tabular if blended.get(n)]
            width = hmtx[blended_tabular[0]][0] if blended_tabular else old_advance[next(iter(tabular))]
            enforce_tabular(master, sorted(tabular), width)
        blended_set = master.getGlyphSet()
        master["OS/2"].sxHeight = round(height(blended_set, master, "x"))
        master["OS/2"].sCapHeight = round(height(blended_set, master, "H"))
        src = SourceDescriptor()
        src.font = master
        src.location = {"Weight": w}
        src.name = f"master-{w:g}"
        ds.addSource(src)

    print(
        f"[{key}] blended {len(blended) - len(swapped)} glyphs; took the second font's drawing for "
        f"{len(swapped)} and kept Geist's for {len(kept)} it could not match"
    )
    for name, why in sorted(swapped.items()):
        print(f"[{key}]   second font {name}: {why}")
    for name, why in sorted(kept.items()):
        print(f"[{key}]   kept {name}: {why}")

    vf, _, _ = build_variable_font(ds)
    vf["STAT"] = base["STAT"]
    vf["fvar"].instances = base["fvar"].instances
    for table in ("meta", "gasp", "prep"):
        if table in base and table not in vf:
            vf[table] = base[table]
    rename(vf, base, donor, cfg)

    out = ROOT / cfg["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    vf.save(f"{out}.ttf")
    vf.flavor = "woff2"
    vf.save(f"{out}.woff2")
    print(f"[{key}] wrote {out}.ttf and .woff2")


def main():
    only = sys.argv[1:]
    try:
        for key, cfg in FAMILIES.items():
            if not only or key in only:
                build_family(key, cfg)
    except BuildError as error:
        print(f"error: {error}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
