// Chart history per (symbol, range). 5D comes with every snapshot; 1D, 1M and 1Y are fetched from
// /api/history the first time a range is opened for a symbol, then kept. 1D (and a failed fetch) is
// retried after 5 minutes.

import { useEffect, useReducer, useRef } from "react";
import { fetchHistory, type Point, type Range, type StockQuote } from "../api";

const MAX_AGE_MS = 5 * 60 * 1000;

interface Entry {
  points: Point[] | null; // null: failed
  at: number; // Date.now() when fetched
}

export type History = { status: "loading" } | { status: "error" } | { status: "ok"; points: Point[] };

/** Swaps the last point for the live price, so intraday charts end where the table does. */
function withLive(points: Point[], price: number | null): Point[] {
  if (price == null || !points.length) return points;
  return [...points.slice(0, -1), { ...points[points.length - 1], close: price }];
}

export function useHistory(q: StockQuote | undefined, range: Range): History {
  const cache = useRef(new Map<string, Entry>());
  const inFlight = useRef(new Set<string>());
  const [, rerender] = useReducer((x: number) => x + 1, 0);
  const symbol = q?.symbol;
  const key = `${symbol}|${range}`;
  const entry = cache.current.get(key);
  const stale = entry != null && (range === "1D" || !entry.points) && Date.now() - entry.at > MAX_AGE_MS;

  useEffect(() => {
    if (!symbol || range === "5D" || (entry && !stale) || inFlight.current.has(key)) return;
    inFlight.current.add(key);
    fetchHistory(symbol, range)
      .then((points) => ({ points, at: Date.now() }))
      .catch(() => ({ points: entry?.points ?? null, at: Date.now() })) // keep old points on a failed refetch
      .then((e) => {
        cache.current.set(key, e);
        inFlight.current.delete(key);
        rerender();
      });
  }, [symbol, range, key, entry, stale]);

  if (!q) return { status: "error" };
  if (range === "5D") {
    return q.history_5d.length ? { status: "ok", points: withLive(q.history_5d, q.price) } : { status: "error" };
  }
  if (!entry) return { status: "loading" };
  if (!entry.points?.length) return { status: "error" };
  return { status: "ok", points: range === "1D" ? withLive(entry.points, q.price) : entry.points };
}
