"""Make two different outlines of the same letter compatible, then interpolate.

Two typefaces never share point structure, so a letter from each cannot be
averaged directly. For every contour pair this module:

1. pairs contours by position and orientation,
2. rotates the donor contour so both start at corresponding points,
3. matches corners in order (an alignment, so extra corners on one side are
   allowed), and uses them as anchors,
4. splits both contours at every node of either one, measured by arc length
   between anchors, so each piece has a partner,
5. interpolates the paired cubic pieces.

The plan (pairing, rotation, split parameters) is computed once at the default
master and replayed at every other master, so the blended glyph has the same
structure everywhere and still varies along the weight axis.
"""

from __future__ import annotations

import itertools
import math

from fontTools.cu2qu import curves_to_quadratic
from fontTools.pens.basePen import BasePen

CORNER_DEGREES = 30
SKIP_COST = 0.12  # Cost of leaving a corner unmatched, as a fraction of the contour box.
MATCH_LIMIT = 0.25  # Corners further apart than this (box fraction) never pair.
MERGE_TOLERANCE = 0.03  # Nodes this close (as a span fraction) are one feature.
ROTATION_TIE = 4.0  # Start rotations scoring within this factor of the best are near ties...
ROTATION_SLACK = 0.5  # ...or within this much of it (sum of squared box distances, 64 samples).
START_GAP = 0.05  # A near tie replaces the best only when its start is this much closer (box fraction).
SAMPLES = 24
OVERLAP_TOLERANCE = 0.002  # Union changes ink area by more than this fraction only when strokes overlap.


class Incompatible(Exception):
    pass


# --- outlines as cubic segments -------------------------------------------


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


class SegmentPen(BasePen):
    """Collects contours as lists of ('L'|'C', p0, c1, c2, p3) cubic segments."""

    def __init__(self):
        super().__init__(None)
        self.contours = []
        self._segments = None

    def _moveTo(self, pt):
        self._segments = []
        self._start = self._last = pt

    def _lineTo(self, pt):
        p0 = self._last
        self._segments.append(("L", p0, lerp(p0, pt, 1 / 3), lerp(p0, pt, 2 / 3), pt))
        self._last = pt

    def _qCurveToOne(self, p1, p2):
        p0 = self._last
        c1 = (p0[0] + 2 / 3 * (p1[0] - p0[0]), p0[1] + 2 / 3 * (p1[1] - p0[1]))
        c2 = (p2[0] + 2 / 3 * (p1[0] - p2[0]), p2[1] + 2 / 3 * (p1[1] - p2[1]))
        self._segments.append(("C", p0, c1, c2, p2))
        self._last = p2

    def _curveToOne(self, p1, p2, p3):
        self._segments.append(("C", self._last, p1, p2, p3))
        self._last = p3

    def _closePath(self):
        # Always close with an explicit (possibly zero-length) line so every
        # master has the same segment count.
        self._lineTo(self._start)
        self.contours.append(self._segments)
        self._segments = None

    _endPath = _closePath


def segments_of(draw):
    pen = SegmentPen()
    draw(pen)
    return pen.contours


def merged(draw):
    """A draw function for the outline with overlapping contours unioned."""
    import pathops

    path = pathops.Path()
    draw(path.getPen())
    path = pathops.simplify(path, fix_winding=True, keep_starting_points=True, clockwise=True)
    return path.draw


def _nearest_on(seg, p):
    """Parameter and distance of the point on `seg` closest to `p`."""
    best_t, best_d = 0.0, math.inf
    for i in range(SAMPLES + 1):
        t = i / SAMPLES
        d = math.dist(point_at(seg, t), p)
        if d < best_d:
            best_t, best_d = t, d
    step = 1 / SAMPLES
    for _ in range(30):
        step /= 2
        for t in (best_t - step, best_t + step):
            if 0 <= t <= 1:
                d = math.dist(point_at(seg, t), p)
                if d < best_d:
                    best_t, best_d = t, d
    return best_t, best_d


def _locations(contours, p, tolerance):
    """Every place (contour, segment, t) where `p` lies on the outline."""
    found = []
    for ci, contour in enumerate(contours):
        for si, seg in enumerate(contour):
            if seg[1] == seg[4]:
                continue
            t, d = _nearest_on(seg, p)
            if d <= tolerance:
                found.append((ci, si, t))
    return found


def _intersect(seg_a, t, seg_b, u):
    """Refine where two segments cross, starting from (t, u)."""
    h = 1e-6
    for _ in range(50):
        pa, pb = point_at(seg_a, t), point_at(seg_b, u)
        fx, fy = pa[0] - pb[0], pa[1] - pb[1]
        if abs(fx) + abs(fy) < 1e-7:
            break
        qa, qb = point_at(seg_a, t + h), point_at(seg_b, u + h)
        da = ((qa[0] - pa[0]) / h, (qa[1] - pa[1]) / h)
        db = ((qb[0] - pb[0]) / h, (qb[1] - pb[1]) / h)
        # Solve da*dt - db*du = -f.
        det = -da[0] * db[1] + db[0] * da[1]
        if abs(det) < 1e-9:
            raise Incompatible("overlapping strokes meet at a tangent")
        dt = (-fx * -db[1] - -db[0] * -fy) / det
        du = (da[0] * -fy - da[1] * -fx) / det
        t, u = t + dt, u + du
    else:
        raise Incompatible("overlapping strokes stop crossing between masters")
    if not (-1e-6 <= t <= 1 + 1e-6 and -1e-6 <= u <= 1 + 1e-6):
        raise Incompatible("overlapping strokes stop crossing between masters")
    return min(max(t, 0.0), 1.0), min(max(u, 0.0), 1.0)


def _forward(n, start, end):
    """Distance from `start` to `end` going forward round a contour of n segments,
    with positions written as segment index plus t."""
    return (end - start) % n


def union_plan(contours, union, tolerance=0.5):
    """Describe a union of overlapping contours in terms of the drawn ones, so
    the same union can be rebuilt at every master with one point structure.

    pathops rewrites points differently at each weight (joining curves and
    dropping collinear nodes), which breaks interpolation. Instead each union
    contour becomes a walk along the drawn contours. A node of the walk is a
    point on one drawn contour, or the crossing of two, which is solved again
    at every master."""
    plan = []
    for ucontour in union:
        live = [seg for seg in ucontour if seg[1] != seg[4]]
        nodes = []
        for seg in live:
            locs = _locations(contours, seg[1], tolerance)
            if not locs:
                raise Incompatible("union point is off the drawn outline")
            # A crossing sits on two places that are not the same point of one contour.
            cross = None
            for i, (ci, si, t) in enumerate(locs):
                for cj, sj, u in locs[i + 1 :]:
                    n = len(contours[ci])
                    same = ci == cj and min(_forward(n, si + t, sj + u), _forward(n, sj + u, si + t)) < 1e-3
                    if not same and 1e-3 < t < 1 - 1e-3 and 1e-3 < u < 1 - 1e-3:
                        cross = ((ci, si), (cj, sj))
                        break
                if cross:
                    break
            nodes.append({"locs": locs, "cross": cross})
        pieces = []
        for i, seg in enumerate(live):
            mid = point_at(seg, 0.5)
            here, there = nodes[i], nodes[(i + 1) % len(live)]
            best = None
            for ci, si, t in here["locs"]:
                n = len(contours[ci])
                for cj, sj, u in there["locs"]:
                    if cj != ci:
                        continue
                    span = _forward(n, si + t, sj + u)
                    for _, sm, tm in _locations([contours[ci]], mid, tolerance):
                        if 0 < _forward(n, si + t, sm + tm) < span and (best is None or span < best[0]):
                            best = (span, ci, (si, t), (sj, u))
            if best is None:
                raise Incompatible("union edge does not follow one drawn contour")
            _, ci, (si, t), (sj, u) = best
            n = len(contours[ci])
            # The drawn segments this edge runs along, with how each end is found.
            ks = [si]
            while ks[-1] != sj or (len(ks) == 1 and sj == si and u < t):
                ks.append((ks[-1] + 1) % n)
                if len(ks) > n + 1:
                    raise Incompatible("union edge does not follow one drawn contour")
            for idx, k in enumerate(ks):
                start = ("node", i) if idx == 0 else ("const", 0.0)
                end = ("node", (i + 1) % len(live)) if idx == len(ks) - 1 else ("const", 1.0)
                pieces.append((ci, k, start, end))
        contour_plan = {"nodes": nodes, "pieces": pieces}
        # Drop pieces that are empty here and stay empty at every master: both
        # ends fixed (a drawn node, not a crossing) and equal.
        kept = []
        for piece in pieces:
            ci, k, start, end = piece
            a, b = _piece_range(contours, contour_plan, piece)
            fixed = all(ref[0] == "const" or not nodes[ref[1]]["cross"] for ref in (start, end))
            if b - a > 1e-9 or not fixed:
                kept.append(piece)
        contour_plan["pieces"] = kept
        plan.append(contour_plan)
    rebuilt = apply_union(plan, contours)
    if abs(ink_area(rebuilt) - ink_area(union)) > OVERLAP_TOLERANCE * max(abs(ink_area(union)), 1.0):
        raise Incompatible("rebuilt union does not match the overlap removal")
    return plan


def _piece_range(contours, contour_plan, piece):
    ci, k, start, end = piece
    nodes = contour_plan["nodes"]
    a = start[1] if start[0] == "const" else _node_t(contours, nodes[start[1]], ci, k)
    b = end[1] if end[0] == "const" else _node_t(contours, nodes[end[1]], ci, k)
    return a, b


def _node_t(contours, node, ci, k):
    """A node's parameter on drawn segment (ci, k) at this master."""
    if node["cross"]:
        (ca, sa), (cb, sb) = node["cross"]
        t0 = next(t for c, s_, t in node["locs"] if (c, s_) == (ca, sa))
        u0 = next(t for c, s_, t in node["locs"] if (c, s_) == (cb, sb))
        t, u = _intersect(contours[ca][sa], t0, contours[cb][sb], u0)
        if (ci, k) == (ca, sa):
            return t
        if (ci, k) == (cb, sb):
            return u
    for c, s_, t in node["locs"]:
        if (c, s_) == (ci, k):
            return t
    raise Incompatible("union node is not on its drawn segment")


def apply_union(plan, contours):
    """Rebuild a planned union from one master's drawn contours. Every master
    gets the same pieces, so the result interpolates."""
    out = []
    for contour_plan in plan:
        segments = []
        for piece in contour_plan["pieces"]:
            ci, k = piece[:2]
            a, b = _piece_range(contours, contour_plan, piece)
            seg = contours[ci][k]
            if b < a:
                raise Incompatible("overlapping strokes stop crossing between masters")
            segments.append(sub_curve(seg, a, b) if b > a else ("L", point_at(seg, a), point_at(seg, a), point_at(seg, a), point_at(seg, a)))
        out.append(segments)
    return out


def overlaps(contours, union):
    """Whether unioning changes the filled shape, meaning strokes overlap.
    Union also rewrites points (it joins curves and drops collinear nodes
    differently at each weight), so callers use it only where this holds."""
    drawn, filled = ink_area(contours), ink_area(union)
    return abs(drawn - filled) > OVERLAP_TOLERANCE * max(abs(drawn), 1.0)


def same_structure(per_master_contours):
    """True when every master has the same contours with the same segment kinds."""
    shapes = {tuple(tuple(seg[0] for seg in c) for c in contours) for contours in per_master_contours}
    return len(shapes) == 1


def point_at(seg, t):
    _, p0, c1, c2, p3 = seg
    mt = 1 - t
    return (
        mt**3 * p0[0] + 3 * mt * mt * t * c1[0] + 3 * mt * t * t * c2[0] + t**3 * p3[0],
        mt**3 * p0[1] + 3 * mt * mt * t * c1[1] + 3 * mt * t * t * c2[1] + t**3 * p3[1],
    )


def length_table(seg):
    pts = [point_at(seg, i / SAMPLES) for i in range(SAMPLES + 1)]
    table = [0.0]
    for a, b in zip(pts, pts[1:]):
        table.append(table[-1] + math.dist(a, b))
    return table


def sub_curve(seg, t0, t1):
    """The part of a cubic between t0 and t1, exact at the ends."""
    kind, p0, c1, c2, p3 = seg
    if t1 < 1:
        a, b, c = lerp(p0, c1, t1), lerp(c1, c2, t1), lerp(c2, p3, t1)
        d, e = lerp(a, b, t1), lerp(b, c, t1)
        p0, c1, c2, p3 = p0, a, d, lerp(d, e, t1)
    if t0 > 0:
        u = t0 / t1
        a, b, c = lerp(p0, c1, u), lerp(c1, c2, u), lerp(c2, p3, u)
        d, e = lerp(a, b, u), lerp(b, c, u)
        p0, c1, c2 = lerp(d, e, u), e, c
    return (kind, p0, c1, c2, p3)


def reverse_contour(segments):
    return [(k, p3, c2, c1, p0) for k, p0, c1, c2, p3 in reversed(segments)]


def signed_area(segments):
    pts = [point_at(s, i / 8) for s in segments for i in range(8)]
    return sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(pts, pts[1:] + pts[:1])) / 2


class Contour:
    """Arc-length bookkeeping for one contour."""

    def __init__(self, segments):
        self.segments = segments
        self.tables = [length_table(s) for s in segments]
        self.starts = []
        total = 0.0
        for table in self.tables:
            self.starts.append(total)
            total += table[-1]
        self.length = total or 1.0

    def nodes(self):
        """Normalized arc position of the start of each segment."""
        return [s / self.length for s in self.starts]

    def locate(self, pos, hint=None):
        """Segment index and t for a normalized arc position."""
        s = pos * self.length
        if hint is None:
            hint = max(i for i, start in enumerate(self.starts) if start <= s + 1e-9)
        table = self.tables[hint]
        local = s - self.starts[hint]
        if table[-1] <= 0:
            return hint, 0.0
        if local <= 0:
            return hint, 0.0
        if local >= table[-1]:
            return hint, 1.0
        for i in range(SAMPLES):
            if table[i + 1] >= local:
                span = table[i + 1] - table[i]
                frac = (local - table[i]) / span if span else 0
                return hint, (i + frac) / SAMPLES
        return hint, 1.0

    def sample(self, count):
        out = []
        for i in range(count):
            idx, t = self.locate(i / count)
            out.append(point_at(self.segments[idx], t))
        return out

    def corners(self):
        result = []
        n = len(self.segments)
        for i in range(n):
            if self.tables[i][-1] <= 1e-6:
                continue
            j = i - 1
            while j > i - n and self.tables[j % n][-1] <= 1e-6:
                j -= 1
            seg = self.segments[i]
            if _is_corner(self.segments[j % n], seg):
                result.append((self.starts[i] / self.length, seg[1]))
        return result


def _is_corner(prev, seg):
    """Whether the outline turns sharply where `prev` ends and `seg` starts."""
    tin = _tangent_in(prev)
    tout = _tangent_out(seg)
    if tin is None or tout is None:
        return False
    cos = (tin[0] * tout[0] + tin[1] * tout[1]) / (math.hypot(*tin) * math.hypot(*tout))
    return cos < math.cos(math.radians(CORNER_DEGREES))


def _tangent_in(seg):
    _, p0, c1, c2, p3 = seg
    for q in (c2, c1, p0):
        v = (p3[0] - q[0], p3[1] - q[1])
        if abs(v[0]) + abs(v[1]) > 1e-6:
            return v
    return None


def _tangent_out(seg):
    _, p0, c1, c2, p3 = seg
    for q in (c1, c2, p3):
        v = (q[0] - p0[0], q[1] - p0[1])
        if abs(v[0]) + abs(v[1]) > 1e-6:
            return v
    return None


# --- planning --------------------------------------------------------------


def _center(segments):
    xs = [p[0] for s in segments for p in s[1:]]
    ys = [p[1] for s in segments for p in s[1:]]
    return ((min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2)


def _pair_contours(a_contours, b_contours):
    n = len(a_contours)
    if n != len(b_contours):
        raise Incompatible(f"{n} contours against {len(b_contours)}")
    a_info = [(_center(c), signed_area(c) < 0) for c in a_contours]
    b_info = [(_center(c), signed_area(c) < 0) for c in b_contours]

    def cost(i, j):
        (ca, oa), (cb, ob) = a_info[i], b_info[j]
        return math.dist(ca, cb) + (0 if oa == ob else 5000)

    if n <= 6:
        best = min(itertools.permutations(range(n)), key=lambda p: sum(cost(i, p[i]) for i in range(n)))
    else:
        free, best = set(range(n)), []
        for i in range(n):
            j = min(free, key=lambda j: cost(i, j))
            free.remove(j)
            best.append(j)
    if any(a_info[i][1] != b_info[best[i]][1] for i in range(n)):
        raise Incompatible("contour orientations do not pair up")
    return list(best)


def _frame(segments):
    """Maps points into the contour's own bounding box, so two letters that
    differ in width or position can still be compared feature by feature."""
    xs = [p[0] for s in segments for p in s[1:]]
    ys = [p[1] for s in segments for p in s[1:]]
    x0, y0 = min(xs), min(ys)
    w, h = max(max(xs) - x0, 1.0), max(max(ys) - y0, 1.0)
    return lambda p: ((p[0] - x0) / w, (p[1] - y0) / h)


def _best_rotation(a, b_segments):
    fa, fb = _frame(a.segments), _frame(b_segments)
    a_pts = [fa(p) for p in Contour(a.segments).sample(64)]
    scores = []
    for k, table in enumerate(length_table(s) for s in b_segments):
        if table[-1] <= 1e-6:
            continue
        rotated = Contour(b_segments[k:] + b_segments[:k])
        score = sum(math.dist(p, fb(q)) ** 2 for p, q in zip(a_pts, rotated.sample(64)))
        scores.append((score, k))
    best_score, best_k = min(scores)
    # Arc-length sampling can rank a start one short edge away from the
    # matching corner first: in the m it picked the bottom right of the left
    # stem against Geist's bottom left, which blends a spike into the stem.
    # When A starts on a corner, take the near-tied corner start that sits
    # where A's does. A start on a smooth curve keeps the shape score's pick.
    if not _is_corner(a.segments[-1], a.segments[0]):
        return best_k
    start = fa(a.segments[0][1])
    tie = max(best_score * ROTATION_TIE, best_score + ROTATION_SLACK)
    near = [k for score, k in scores if score <= tie and _is_corner(b_segments[k - 1], b_segments[k])]
    if not near:
        return best_k

    def start_gap(k):
        return math.dist(start, fb(b_segments[k][1]))

    pick = min(near, key=start_gap)
    return pick if start_gap(best_k) - start_gap(pick) > START_GAP else best_k


def _align_corners(ca, cb, fa, fb):
    """Order-preserving corner matching (sequence alignment) in each
    contour's own frame."""
    ca = [(s, fa(p)) for s, p in ca]
    cb = [(s, fb(p)) for s, p in cb]
    n, m = len(ca), len(cb)
    em = 1.0
    skip = SKIP_COST * em
    dp = [[0.0] * (m + 1) for _ in range(n + 1)]
    move = [[None] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        dp[i][0], move[i][0] = i * skip, "a"
    for j in range(1, m + 1):
        dp[0][j], move[0][j] = j * skip, "b"
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            d = math.dist(ca[i - 1][1], cb[j - 1][1])
            options = [(dp[i - 1][j] + skip, "a"), (dp[i][j - 1] + skip, "b")]
            if d < MATCH_LIMIT * em:
                options.append((dp[i - 1][j - 1] + d, "m"))
            dp[i][j], move[i][j] = min(options)
    pairs, i, j = [], n, m
    while i or j:
        step = move[i][j]
        if step == "m":
            pairs.append((ca[i - 1][0], cb[j - 1][0]))
            i, j = i - 1, j - 1
        elif step == "a":
            i -= 1
        else:
            j -= 1
    return sorted(p for p in pairs if 0 < p[0] < 1 and 0 < p[1] < 1)


def _breakpoints(a, b, anchors):
    a_nodes, b_nodes = a.nodes(), b.nodes()
    points = []
    spans = [(0.0, 0.0)] + anchors + [(1.0, 1.0)]
    for (a0, b0), (a1, b1) in zip(spans, spans[1:]):
        points.append((a0, b0))
        events = []
        for s in a_nodes:
            if a0 + 1e-9 < s < a1 - 1e-9:
                events.append(((s - a0) / (a1 - a0), "a", s))
        for s in b_nodes:
            if b0 + 1e-9 < s < b1 - 1e-9:
                events.append(((s - b0) / (b1 - b0), "b", s))
        events.sort()
        i = 0
        while i < len(events):
            u, side, s = events[i]
            if i + 1 < len(events) and events[i + 1][1] != side and events[i + 1][0] - u < MERGE_TOLERANCE:
                other = events[i + 1]
                pa, pb = (s, other[2]) if side == "a" else (other[2], s)
                points.append((pa, pb))
                i += 2
                continue
            if side == "a":
                points.append((s, b0 + u * (b1 - b0)))
            else:
                points.append((a0 + u * (a1 - a0), s))
            i += 1
    points.append((1.0, 1.0))
    return points


def _pieces(contour, positions):
    out = []
    for p0, p1 in zip(positions, positions[1:]):
        if p1 - p0 <= 1e-9:
            # Zero length on this side: the piece collapses to the point here.
            idx, t = contour.locate(p0)
            out.append((idx, t, t))
            continue
        idx, _ = contour.locate((p0 + p1) / 2)
        _, t0 = contour.locate(p0, idx)
        _, t1 = contour.locate(p1, idx)
        out.append((idx, t0, t1))
    return out


def plan_glyph(a_contours, b_contours, em):
    """Build a replayable plan from the default master's outlines."""
    pairing = _pair_contours(a_contours, b_contours)
    plan = []
    for ai, bi in enumerate(pairing):
        a = Contour(a_contours[ai])
        b_segments = b_contours[bi]
        reverse = (signed_area(a.segments) < 0) != (signed_area(b_segments) < 0)
        if reverse:
            b_segments = reverse_contour(b_segments)
        rotation = _best_rotation(a, b_segments)
        b = Contour(b_segments[rotation:] + b_segments[:rotation])
        anchors = _align_corners(a.corners(), b.corners(), _frame(a.segments), _frame(b.segments))
        points = _breakpoints(a, b, anchors)
        a_pieces = _pieces(a, [p[0] for p in points])
        b_pieces = _pieces(b, [p[1] for p in points])
        pieces = []
        for pa, pb in zip(a_pieces, b_pieces):
            if pa[1] == pa[2] and pb[1] == pb[2]:
                continue
            is_line = a.segments[pa[0]][0] == "L" and b.segments[pb[0]][0] == "L"
            pieces.append((pa, pb, is_line))
        plan.append({"b": bi, "reverse": reverse, "rotation": rotation, "pieces": pieces})
    return plan


# --- replay ----------------------------------------------------------------


def blend_contours(plan, a_contours, b_contours, t):
    """Interpolated cubic pieces for every contour, following the plan."""
    out = []
    for ai, step in enumerate(plan):
        b_segments = b_contours[step["b"]]
        if step["reverse"]:
            b_segments = reverse_contour(b_segments)
        k = step["rotation"]
        b_segments = b_segments[k:] + b_segments[:k]
        a_segments = a_contours[ai]
        pieces = []
        for (ia, a0, a1), (ib, b0, b1), is_line in step["pieces"]:
            ca = sub_curve(a_segments[ia], a0, a1) if a1 > a0 else _point_curve(a_segments[ia], a0)
            cb = sub_curve(b_segments[ib], b0, b1) if b1 > b0 else _point_curve(b_segments[ib], b0)
            mixed = tuple(lerp(p, q, t) for p, q in zip(ca[1:], cb[1:]))
            pieces.append((is_line, mixed))
        # Close exactly: the last piece ends where the first begins.
        start = pieces[0][1][0]
        last_line, last = pieces[-1]
        pieces[-1] = (last_line, (last[0], last[1], last[2], start))
        out.append(pieces)
    return out


def _polyline(pieces, steps=8):
    pts = []
    for _, (p0, c1, c2, p3) in pieces:
        seg = ("C", p0, c1, c2, p3)
        pts.extend(point_at(seg, i / steps) for i in range(steps))
    return pts


def _crossings(pts):
    """Count proper crossings between non-adjacent edges of a closed polyline."""
    n = len(pts)
    edges = [(pts[i], pts[(i + 1) % n]) for i in range(n)]
    boxes = [
        (min(a[0], b[0]), min(a[1], b[1]), max(a[0], b[0]), max(a[1], b[1])) for a, b in edges
    ]

    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return (v > 1e-9) - (v < -1e-9)

    count = 0
    for i in range(n):
        bi = boxes[i]
        for j in range(i + 2, n):
            if i == 0 and j == n - 1:
                continue
            bj = boxes[j]
            if bi[2] < bj[0] or bj[2] < bi[0] or bi[3] < bj[1] or bj[3] < bi[1]:
                continue
            (p1, p2), (q1, q2) = edges[i], edges[j]
            if orient(p1, p2, q1) * orient(p1, p2, q2) < 0 and orient(q1, q2, p1) * orient(q1, q2, p2) < 0:
                count += 1
    return count


def self_crossings(contours_pieces):
    return [_crossings(_polyline(pieces)) for pieces in contours_pieces]


def source_crossings(contours):
    """Crossings of source contours, in the same units as self_crossings."""
    return [
        _crossings(_polyline([(k == "L", (p0, c1, c2, p3)) for k, p0, c1, c2, p3 in c if p0 != p3 or k != "L"]))
        for c in contours
    ]


def ink_area(contours):
    """Filled area, counting counters as negative (TrueType winding)."""
    return -sum(signed_area(c) for c in contours)


def area_ratio(blended, a_contours, b_contours, mix=0.5):
    """Blended ink area against the sources' areas mixed at the same ratio, as
    (ratio, absolute drift in square units). Matched structures stay within a
    couple of percent; letters whose parts differ (a tall hook against a short
    one) swell or shrink well past that."""
    mixed = [[("C",) + piece for _, piece in contour] for contour in blended]
    expected = ink_area(a_contours) * (1 - mix) + ink_area(b_contours) * mix
    actual = ink_area(mixed)
    return (actual / expected if expected else 1.0), abs(actual - expected)


def _point_curve(seg, t):
    p = point_at(seg, t)
    return ("L", p, p, p, p)


def draw_compatible(pens, blended_by_master, max_error=1.0):
    """Draw one glyph into a pen per master with identical point structure."""
    contour_count = len(blended_by_master[0])
    for ci in range(contour_count):
        piece_count = len(blended_by_master[0][ci])
        starts = [m[ci][0][1][0] for m in blended_by_master]
        for pen, start in zip(pens, starts):
            pen.moveTo(start)
        for pi in range(piece_count):
            is_line = blended_by_master[0][ci][pi][0]
            curves = [m[ci][pi][1] for m in blended_by_master]
            if is_line:
                for pen, curve in zip(pens, curves):
                    pen.lineTo(curve[3])
                continue
            splines = curves_to_quadratic([list(c) for c in curves], [max_error] * len(curves))
            for pen, spline in zip(pens, splines):
                pen.qCurveTo(*spline[1:])
        for pen in pens:
            pen.closePath()
