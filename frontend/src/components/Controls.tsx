import type { Timeframe } from "../api";

interface Props {
  timeframe?: Timeframe;
  onTimeframe?: (t: Timeframe) => void;
  topN?: number;
  onTopN?: (n: number) => void;
  topNOptions?: number[];
}

const TFS: Timeframe[] = ["1d", "1w", "1m"];

export default function Controls({
  timeframe,
  onTimeframe,
  topN,
  onTopN,
  topNOptions = [10, 20, 50, 100, 200],
}: Props) {
  return (
    <div className="controls">
      {onTimeframe && (
        <div className="control">
          <label>Timeframe</label>
          <div className="segmented">
            {TFS.map((t) => (
              <button
                key={t}
                className={t === timeframe ? "on" : ""}
                onClick={() => onTimeframe(t)}
              >
                {t}
              </button>
            ))}
          </div>
        </div>
      )}
      {onTopN && (
        <div className="control">
          <label>Show top</label>
          <select value={topN} onChange={(e) => onTopN(Number(e.target.value))}>
            {topNOptions.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  );
}
