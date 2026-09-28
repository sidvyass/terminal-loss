// Types for GET /api/snapshot and /api/history; mirrors src/terminal_loss/api/schema.py.

export interface Point {
  t: string; // ISO timestamp in exchange time
  close: number;
}

export interface Quote {
  name: string;
  symbol: string;
  price: number | null;
  prev_close: number | null;
  day_low: number | null;
  day_high: number | null;
  year_low: number | null;
  year_high: number | null;
  volume: number | null;
  avg_volume: number | null; // 3-month average daily volume
  error: string | null;
  history_5d: Point[]; // ~5 days of hourly closes
  timezone: string | null; // exchange time zone, e.g. "America/New_York"
}

export interface StockQuote extends Quote {
  group: string | null; // config group label, e.g. "INDEX & ETF"
}

export interface ExtraQuote extends Quote {
  label: string; // e.g. "Treasury yield"; `name` holds the key ("US 10Y")
}

export const METRICS = ["gdp_growth", "unemployment", "inflation", "interest_rate", "debt_to_gdp"] as const;
export type Metric = (typeof METRICS)[number];

export interface Stat {
  value: number;
  period: string; // year for IMF data, date for BIS
  stale: boolean;
}

export interface Country {
  name: string;
  currency: string;
  currency_symbol: string;
  fx_symbol: string | null;
  fx_rate: number | null; // local currency per USD
  bis: string;
  central_bank: string | null;
  stats: Partial<Record<Metric, Stat | null>>;
  history: Partial<Record<Metric, [number, number][]>>; // IMF metrics only
}

export interface Snapshot {
  quotes: StockQuote[];
  extras: ExtraQuote[];
  countries: Country[];
  macro_fetched_at: number | null; // epoch seconds
}

export async function fetchSnapshot(force = false): Promise<Snapshot> {
  const resp = await fetch(force ? "/api/snapshot?force=true" : "/api/snapshot");
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.json();
}

export type Range = "1D" | "5D" | "1M" | "1Y";
export const RANGES: Range[] = ["1D", "5D", "1M", "1Y"];

export async function fetchHistory(symbol: string, range: Range): Promise<Point[]> {
  const resp = await fetch(`/api/history?${new URLSearchParams({ symbol, range })}`);
  if (!resp.ok) throw new Error(`API ${resp.status}`);
  return resp.json();
}

export function change(q: Quote): number | null {
  return q.price == null || q.prev_close == null ? null : q.price - q.prev_close;
}

export function pctChange(q: Quote): number | null {
  const c = change(q);
  return c == null || !q.prev_close ? null : (c / q.prev_close) * 100;
}
