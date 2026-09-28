// Detail-chart series: values, hover labels and x ticks per range, plus the y scale and SVG paths.
// Timestamps are shown in the exchange's time zone.

import type { Point, Range } from "../api";
import { compact, fmt, niceStep } from "../format";

export interface Series {
  vals: number[];
  labels: string[]; // hover label per point
  ticks: { i: number; label: string }[]; // x-axis labels
  base: number; // dashed baseline; the range return is measured against it
}

interface Parts {
  weekday: string;
  month: string;
  day: string;
  year: string;
  hour: string;
  minute: string;
}

function partsIn(timeZone: string | null): (iso: string) => Parts {
  const f = new Intl.DateTimeFormat("en-US", {
    timeZone: timeZone ?? undefined,
    weekday: "short",
    month: "short",
    day: "numeric",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hourCycle: "h23",
  });
  return (iso) => Object.fromEntries(f.formatToParts(new Date(iso)).map((p) => [p.type, p.value])) as unknown as Parts;
}

const MIN_TICK_GAP = 0.06; // fraction of the width; closer x labels would overlap

export function buildSeries(points: Point[], range: Range, prevClose: number | null, timeZone: string | null): Series {
  const vals = points.map((p) => p.close);
  const toParts = partsIn(timeZone);
  const parts = points.map((p) => toParts(p.t));
  const n = vals.length;
  const hhmm = (p: Parts) => `${p.hour}:${p.minute}`;
  const md = (p: Parts) => `${p.month} ${p.day}`;
  let labels: string[];
  let ticks: { i: number; label: string }[] = [];

  if (range === "1D") {
    labels = parts.map(hhmm);
    const step = Math.max(1, Math.round((n * 18) / 78)); // every 90 min for a full 5-minute session
    for (let i = 0; i < n; i += step) ticks.push({ i, label: labels[i] });
  } else if (range === "5D") {
    labels = parts.map((p) => `${p.weekday} ${hhmm(p)}`);
    // Weekday name at the middle of each day's points.
    let start = 0;
    for (let i = 1; i <= n; i++) {
      const p = parts[start];
      if (i === n || md(parts[i]) !== md(p)) {
        ticks.push({ i: Math.floor((start + i - 1) / 2), label: p.weekday });
        start = i;
      }
    }
  } else if (range === "1M") {
    labels = parts.map(md);
    for (let i = 0; i < n; i += 5) ticks.push({ i, label: labels[i] });
  } else {
    labels = parts.map((p) => `${md(p)}, ${p.year}`);
    // Short month name at every other month boundary.
    const boundaries = parts.flatMap((p, i) => (i && p.month !== parts[i - 1].month ? [{ i, label: p.month }] : []));
    ticks = boundaries.filter((_, k) => k % 2 === 0);
  }

  if (n > 1) {
    const kept: typeof ticks = [];
    for (const t of ticks) {
      const last = kept[kept.length - 1];
      if (!last || (t.i - last.i) / (n - 1) >= MIN_TICK_GAP) kept.push(t);
    }
    ticks = kept;
  }
  const base = range === "1D" && prevClose != null ? prevClose : vals[0];
  return { vals, labels, ticks, base };
}

export const W = 1000;
export const H = 300;

export interface Scale {
  x: (i: number) => number; // SVG units, 0..W
  y: (v: number) => number; // SVG units, 0..H
  line: string;
  area: string;
  yTicks: { top: number; label: string }[]; // top in percent
}

/** Y domain [min(vals, base), max(vals, base)] padded 8% each side; gridlines at niceStep((hi-lo)/4). */
export function scale(vals: number[], base: number): Scale {
  let lo = Math.min(...vals, base);
  let hi = Math.max(...vals, base);
  const pad = (hi - lo) * 0.08 || 1;
  lo -= pad;
  hi += pad;
  const n = vals.length;
  const x = (i: number) => (n > 1 ? (i / (n - 1)) * W : W / 2);
  const y = (v: number) => H - ((v - lo) / (hi - lo)) * H;
  const line = vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)} ${y(v).toFixed(1)}`).join("");
  const step = niceStep((hi - lo) / 4);
  const dec = step >= 1 ? 0 : step >= 0.1 ? 1 : 2;
  const yTicks = [];
  for (let k = Math.ceil(lo / step); k * step <= hi; k++) {
    const v = k * step;
    yTicks.push({ top: (y(v) / H) * 100, label: Math.abs(v) >= 10_000 ? compact(v) : fmt(v, dec) });
  }
  return { x, y, line, area: `${line}L${x(n - 1).toFixed(1)} ${H}L${x(0).toFixed(1)} ${H}Z`, yTicks };
}
