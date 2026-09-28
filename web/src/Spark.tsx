import { barHeight } from "./format";

/** Vertical-bar sparkline from levels 0-7; bar width and box height come from the `className`. */
export function Spark({ levels, color, className }: { levels: number[]; color: string; className: string }) {
  return (
    <span className={className}>
      {levels.map((level, i) => (
        <span key={i} style={{ height: `${barHeight(level)}%`, background: color }} />
      ))}
    </span>
  );
}
