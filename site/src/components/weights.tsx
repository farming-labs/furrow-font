const WEIGHTS = [
  [100, "Thin"],
  [200, "ExtraLight"],
  [300, "Light"],
  [400, "Regular"],
  [500, "Medium"],
  [600, "SemiBold"],
  [700, "Bold"],
  [800, "ExtraBold"],
  [900, "Black"],
] as const;

export function Weights() {
  return (
    <div className="weights rows">
      {WEIGHTS.map(([weight, name]) => (
        <div key={weight} className="weight-row">
          <span className="tag tnum">
            {weight} {name}
          </span>
          <span className="weight-sample" style={{ fontWeight: weight }}>
            Readable at every weight.
          </span>
          <span className="weight-mono mono" style={{ fontWeight: weight }} aria-hidden="true">
            {"{ wght: "}
            {weight}
            {" }"}
          </span>
        </div>
      ))}
    </div>
  );
}
