// Number formatting and spark sampling; mirrors the helpers in src/market_cli/ui.py.

export const MINUS = "−";

export function fmt(v: number, digits = 2): string {
  return v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

/** Range-bar label: 612.84, but 82.6k for large values so the column stays narrow. */
export function compact(v: number): string {
  return Math.abs(v) >= 10_000 ? fmt(v / 1000, 1) + "k" : fmt(v);
}

/** Up to 3 decimals, trailing zeros stripped: 3.875 -> "3.875%", 2.300 -> "2.3%". */
export function fpct(v: number): string {
  return String(+v.toFixed(3)) + "%";
}

export function signedChange(v: number): string {
  return v === 0 ? "0.00" : `${v > 0 ? "▲" : "▼"} ${fmt(Math.abs(v))}`;
}

export function signedPct(v: number): string {
  return v === 0 ? "0.00%" : `${v > 0 ? "+" : MINUS}${fmt(Math.abs(v))}%`;
}

/** Marker position in percent along a low..high track, clamped to 0-100. */
export function rangePos(v: number, lo: number, hi: number): number {
  return hi === lo ? 0 : Math.max(0, Math.min(100, ((v - lo) / (hi - lo)) * 100));
}

export function dirColor(v: number | null): string {
  return v == null || v === 0 ? "var(--dim)" : v > 0 ? "var(--up)" : "var(--down)";
}

/** Display form of a Yahoo symbol: ^BSESN -> BSESN, BTC-USD -> BTC. */
export function ticker(symbol: string): string {
  return symbol.replace(/^\^+/, "").replace(/-USD$/, "");
}

/** n evenly spaced samples scaled min-max to levels 0-7 (flat series sit at 3). */
export function sparkLevels(values: number[], n: number): number[] {
  if (!values.length) return [];
  const samples =
    values.length === 1
      ? Array(n).fill(values[0])
      : Array.from({ length: n }, (_, i) => values[Math.round((i * (values.length - 1)) / (n - 1))]);
  const lo = Math.min(...samples);
  const hi = Math.max(...samples);
  if (hi === lo) return Array(n).fill(3);
  return samples.map((v) => Math.round(((v - lo) / (hi - lo)) * 7));
}

/** Bar height in percent for a spark level: 10% floor so the lowest bar stays visible. */
export function barHeight(level: number): number {
  return 10 + (level / 7) * 90;
}
