// Markets tab, "Split" layout: heatmap across the top, stocks table and rates & commodities on the
// left, and the selected stock's detail panel (price chart over four ranges) stretched down the right.
// Phones stack heatmap strip, detail, stocks, then rates & commodities.

import { type PointerEvent, type RefObject, useEffect, useRef, useState } from "react";
import { change, type ExtraQuote, pctChange, RANGES, type StockQuote } from "../api";
import { arrowPct, compact, dirColor, fmt, rangePos, signedChange, signedPct, sparkLevels, ticker } from "../format";
import { revealInStrip, revealOnPhone } from "../mobile";
import { Spark } from "../Spark";
import { QUOTE_SORTS, sortQuotes } from "../sorting";
import type { Dashboard } from "../useDashboard";
import { buildSeries, H, scale, W } from "./series";
import { useHistory } from "./useHistory";

const HIGH_VOLUME = 1.5; // VOL ratio at or above this is highlighted
const ERROR_WIDTH = 14; // max length of an error message in the PRICE cell
const HEAT_FULL = 3; // |% change| at which a heat tile reaches full color

const closes = (q: StockQuote) => q.history_5d.map((p) => p.close);

function volRatio(q: StockQuote): number | null {
  return q.volume && q.avg_volume ? q.volume / q.avg_volume : null; // indices report 0 volume
}

export function Markets({ d, quotes, extras }: { d: Dashboard; quotes: StockQuote[]; extras: ExtraQuote[] }) {
  const ordered = sortQuotes(quotes, d.sort);
  const detailRef = useRef<HTMLElement>(null);
  // A row tap on a phone scrolls up to the detail panel, which sits above the table there.
  const onRowTap = (symbol: string) => {
    d.setSelectedStock(symbol);
    revealOnPhone(detailRef.current);
  };
  return (
    <div className="markets">
      <Heatmap d={d} quotes={ordered} />
      <section className="area-table">
        <div className="panel-head">
          <h2>Stocks</h2>
          <span className="sort-control">
            <span className="kicker">Sort · S</span>
            <span className="seg">
              {QUOTE_SORTS.map(([key, label]) => (
                <button
                  type="button"
                  key={key}
                  className={`seg-opt${d.sort === key ? " active" : ""}`}
                  onClick={() => d.setSort(key)}
                >
                  {label}
                </button>
              ))}
            </span>
          </span>
        </div>
        <StocksTable d={d} quotes={ordered} onSelect={onRowTap} />
      </section>
      <Detail d={d} q={quotes.find((q) => q.symbol === d.selectedStock) ?? quotes[0]} panelRef={detailRef} />
      <section className="area-extras">
        <h2 className="panel-head">Rates &amp; commodities</h2>
        <div className="extras">
          {extras.map((q) => (
            <ExtraCell key={q.symbol} q={q} />
          ))}
        </div>
      </section>
    </div>
  );
}

// ---------------------------------------------------------------- heatmap

function heatBg(pct: number | null): string {
  if (pct == null || Math.abs(pct) < 0.005) return "var(--grid)";
  const t = Math.min(Math.abs(pct) / HEAT_FULL, 1);
  return `color-mix(in srgb, ${pct > 0 ? "var(--up)" : "var(--down)"} ${Math.round(18 + t * 62)}%, var(--bg))`;
}

function Heatmap({ d, quotes }: { d: Dashboard; quotes: StockQuote[] }) {
  const stripRef = useRef<HTMLDivElement>(null);
  // On phones the tiles are one scrolling row; keep the selected one in view when ↑↓ or a row tap
  // changes the selection.
  useEffect(() => {
    const tile = stripRef.current?.querySelector<HTMLElement>(`[data-symbol="${d.selectedStock}"]`);
    revealInStrip(stripRef.current, tile ?? null);
  }, [d.selectedStock]);
  return (
    <section className="area-heat">
      <div className="panel-head">
        <h2>
          Heatmap · 1D<span className="desk-only"> change</span>
        </h2>
        <span className="legend">
          −3%
          <span className="legend-swatches">
            {[-3, -1.5, 0, 1.5, 3].map((p) => (
              <span key={p} style={{ background: heatBg(p) }} />
            ))}
          </span>
          +3%
        </span>
      </div>
      <div className="heat" ref={stripRef}>
        {quotes.map((q) => {
          const pct = q.error ? null : pctChange(q);
          const dark = pct != null && Math.min(Math.abs(pct) / HEAT_FULL, 1) > 0.55;
          return (
            <button
              type="button"
              key={q.symbol}
              data-symbol={q.symbol}
              className={`heat-tile${q.symbol === d.selectedStock ? " selected" : ""}`}
              style={{ background: heatBg(pct), color: dark ? "var(--bg)" : "var(--text)" }}
              onClick={() => d.setSelectedStock(q.symbol)}
            >
              <span className="heat-top">
                <span>{ticker(q.symbol)}</span>
                <span className="heat-price">{q.error || q.price == null ? "N/A" : compact(q.price)}</span>
              </span>
              <span className="heat-pct">{pct == null ? "N/A" : signedPct(pct)}</span>
            </button>
          );
        })}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- stocks table

function StocksTable({
  d,
  quotes,
  onSelect,
}: {
  d: Dashboard;
  quotes: StockQuote[];
  onSelect: (symbol: string) => void;
}) {
  // Grouped: labels in config (snapshot) order. Other sorts: one flat list.
  const sections: { label: string | null; rows: StockQuote[] }[] = [];
  if (d.sort === "group") {
    for (const q of quotes) {
      const label = q.group ?? "";
      const last = sections[sections.length - 1];
      if (last && last.label === label) last.rows.push(q);
      else sections.push({ label, rows: [q] });
    }
  } else {
    sections.push({ label: null, rows: quotes });
  }

  return (
    <>
      <div className="scroller">
        <div className="stocks">
          <div className="stocks-head">
            <span>Symbol</span>
            <span>Name</span>
            <span className="num">Price</span>
            <span className="num">Change</span>
            <span className="num">%</span>
            <span>Day range</span>
            <span>52-week range</span>
            <span className="num amber">Vol</span>
            <span className="num">5 days</span>
          </div>
          {sections.map((s, i) => (
            <div key={s.label ?? i}>
              {s.label != null && <div className="group-label">{s.label}</div>}
              {s.rows.map((q) => (
                <StockRow key={q.symbol} q={q} selected={q.symbol === d.selectedStock} onSelect={onSelect} />
              ))}
            </div>
          ))}
        </div>
      </div>
      <p className="caption desk-only">
        VOL = today's volume vs 3-month average, amber at 1.5× or more · click a row or use ↑↓ to chart it
      </p>
      <p className="caption phone-only">Tap a row or heatmap tile to chart it · drag across the chart to read values</p>
    </>
  );
}

const NA = <span className="na">N/A</span>;

function StockRow({ q, selected, onSelect }: { q: StockQuote; selected: boolean; onSelect: (symbol: string) => void }) {
  const chg = change(q);
  const pct = pctChange(q);
  const props = { className: `stocks-row${selected ? " selected" : ""}`, onClick: () => onSelect(q.symbol) };
  if (q.error || q.price == null || chg == null || pct == null) {
    let message = `error: ${q.error ?? "no data"}`;
    if (message.length > ERROR_WIDTH) message = `${message.slice(0, ERROR_WIDTH - 1)}…`;
    return (
      <div {...props}>
        <span className="sym">{ticker(q.symbol)}</span>
        <span className="name">{q.name}</span>
        <span className="num down nowrap">{message}</span>
        <span className="num">{NA}</span>
        <span className="num">{NA}</span>
        <span>{NA}</span>
        <span>{NA}</span>
        <span className="num">{NA}</span>
        <span className="num">{NA}</span>
      </div>
    );
  }
  const color = dirColor(chg);
  return (
    <div {...props}>
      <span className="sym">{ticker(q.symbol)}</span>
      <span className="name" title={q.name}>
        {q.name}
      </span>
      <span className="price">{fmt(q.price)}</span>
      <span className="num nowrap" style={{ color, fontWeight: 600 }}>
        {signedChange(chg)}
      </span>
      <span className="num" style={{ color, fontWeight: 600 }}>
        {signedPct(pct)}
      </span>
      <RangeBar value={q.price} low={q.day_low} high={q.day_high} marker="var(--amber)" />
      <RangeBar value={q.price} low={q.year_low} high={q.year_high} marker="var(--blue)" />
      <span className="num">
        <Volume q={q} />
      </span>
      <Spark className="spark" levels={sparkLevels(closes(q), 10)} color={chg < 0 ? "var(--down)" : "var(--up)"} />
    </div>
  );
}

function RangeBar({
  value,
  low,
  high,
  marker,
}: {
  value: number;
  low: number | null;
  high: number | null;
  marker: string;
}) {
  if (low == null || high == null) return NA;
  return (
    <span className="range">
      <span>{compact(low)}</span>
      <span className="range-track">
        <span
          className="range-mark"
          style={{ left: `calc(${rangePos(value, low, high)}% - 5px)`, background: marker }}
        />
      </span>
      <span>{compact(high)}</span>
    </span>
  );
}

function Volume({ q }: { q: StockQuote }) {
  const ratio = volRatio(q);
  if (ratio == null) return <span className="vol na">N/A</span>;
  return <span className={`vol${ratio >= HIGH_VOLUME ? " high" : ""}`}>{fmt(ratio, 1)}×</span>;
}

// ---------------------------------------------------------------- detail panel

function Detail({
  d,
  q,
  panelRef,
}: {
  d: Dashboard;
  q: StockQuote | undefined;
  panelRef: RefObject<HTMLElement | null>;
}) {
  const range = d.range;
  const history = useHistory(q, range);
  if (!q) return <aside className="detail" ref={panelRef} />;

  const ok = !q.error && q.price != null;
  const chg = ok ? change(q) : null;
  const pct = ok ? pctChange(q) : null;
  const series = ok && history.status === "ok" ? buildSeries(history.points, range, q.prev_close, q.timezone) : null;
  const last = series?.vals[series.vals.length - 1];
  const ret = series && last != null && series.base ? ((last - series.base) / series.base) * 100 : null;
  const color = ret == null ? "var(--rule)" : ret >= 0 ? "var(--up)" : "var(--down)";
  const ratio = volRatio(q);

  const stats: { label: string; value: string; color?: string; bar?: { pos: number; color: string } }[] = [
    { label: "Prev close", value: q.prev_close == null ? "N/A" : fmt(q.prev_close) },
    {
      label: "Day range",
      value: q.day_low == null || q.day_high == null ? "N/A" : `${compact(q.day_low)} – ${compact(q.day_high)}`,
      bar:
        ok && q.day_low != null && q.day_high != null
          ? { pos: rangePos(q.price!, q.day_low, q.day_high), color: "var(--amber)" }
          : undefined,
    },
    {
      label: "52-week range",
      value: q.year_low == null || q.year_high == null ? "N/A" : `${compact(q.year_low)} – ${compact(q.year_high)}`,
      bar:
        ok && q.year_low != null && q.year_high != null
          ? { pos: rangePos(q.price!, q.year_low, q.year_high), color: "var(--blue)" }
          : undefined,
    },
    (() => {
      const off = ok && q.year_high ? ((q.price! - q.year_high) / q.year_high) * 100 : null;
      return { label: "From 52-week high", value: off == null ? "N/A" : signedPct(off), color: dirColor(off) };
    })(),
    {
      label: `${range} high / low`,
      value: series ? `${compact(Math.max(...series.vals))} / ${compact(Math.min(...series.vals))}` : "N/A",
    },
    {
      label: "Vol vs 3-month avg",
      value: ratio == null ? "N/A" : `${fmt(ratio, 1)}×`,
      color: ratio == null ? "var(--na)" : ratio >= HIGH_VOLUME ? "var(--amber)" : undefined,
    },
  ];

  // Desktop keeps the range control in the head; phones get a full-width one under the price.
  const rangeSeg = (extra: string) => (
    <span className={`seg ${extra}`}>
      {RANGES.map((r) => (
        <button
          type="button"
          key={r}
          className={`seg-opt range-opt${r === range ? " active" : ""}`}
          onClick={() => d.setRange(r)}
        >
          {r}
        </button>
      ))}
    </span>
  );

  return (
    <aside className="detail" style={{ borderTopColor: color }} ref={panelRef}>
      <div className="detail-head">
        <div className="detail-title">
          <span className="detail-name">
            <span className="detail-sym">{ticker(q.symbol)}</span>
            <span className="name">{q.name}</span>
          </span>
          <span className="kicker">{q.group}</span>
        </div>
        {rangeSeg("desk-only")}
      </div>
      <div className="detail-price">
        <span className="detail-last">{ok ? fmt(q.price!) : "N/A"}</span>
        {chg != null && pct != null && (
          <span className="detail-chg" style={{ color: dirColor(chg) }}>
            {signedChange(chg)} {signedPct(pct)}
          </span>
        )}
        <span className="detail-ret">
          {range === "1D" ? "vs prev close" : `${range} return`}{" "}
          <b style={{ color }}>{ret == null ? "N/A" : signedPct(ret)}</b>
        </span>
      </div>
      {rangeSeg("range-seg phone-only")}
      <div className="chart">
        {series ? (
          <Chart key={`${q.symbol}|${range}`} series={series} color={color} />
        ) : (
          <span className={`chart-msg${history.status === "loading" && ok ? "" : " na"}`}>
            {history.status === "loading" && ok ? "Loading…" : "No data"}
          </span>
        )}
      </div>
      <div className="stats">
        {stats.map((s) => (
          <div key={s.label} className="stat">
            <span className="kicker">{s.label}</span>
            <span className="stat-value" style={{ color: s.color }}>
              {s.value}
            </span>
            {s.bar && (
              <span className="stat-track">
                <span style={{ left: `calc(${s.bar.pos}% - 4px)`, background: s.bar.color }} />
              </span>
            )}
          </div>
        ))}
      </div>
    </aside>
  );
}

/** Line + area chart with y gridlines, a dashed baseline and a hover crosshair. Keyed by symbol and
 * range, so the hover clears whenever either changes. */
function Chart({ series, color }: { series: ReturnType<typeof buildSeries>; color: string }) {
  const [hover, setHover] = useState<number | null>(null);
  const { vals, labels, ticks, base } = series;
  const s = scale(vals, base);
  const h = hover != null && hover < vals.length ? hover : null;
  // Pointer events so a finger drag scrubs the chart too; on touch the tooltip stays after lifting.
  const onMove = (e: PointerEvent<HTMLSpanElement>) => {
    const box = e.currentTarget.getBoundingClientRect();
    const f = Math.max(0, Math.min(1, (e.clientX - box.left) / box.width));
    setHover(Math.round(f * (vals.length - 1)));
  };
  return (
    <>
      {s.yTicks.map((t) => (
        <span key={t.label} className="grid-line" style={{ top: `${t.top}%` }}>
          <span className="y-label">{t.label}</span>
        </span>
      ))}
      <span className="base-line" style={{ top: `${(s.y(base) / H) * 100}%` }} />
      <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" aria-hidden="true">
        <path d={s.area} style={{ fill: `color-mix(in srgb, ${color} 14%, transparent)` }} />
        <path d={s.line} vectorEffect="non-scaling-stroke" style={{ fill: "none", stroke: color, strokeWidth: 2 }} />
      </svg>
      {ticks.map((t) => (
        <span key={t.i} className="x-label" style={{ left: `${(s.x(t.i) / W) * 100}%` }}>
          {t.label}
        </span>
      ))}
      {h != null &&
        (() => {
          const left = (s.x(h) / W) * 100;
          const p = ((vals[h] - base) / base) * 100;
          return (
            <>
              <span className="hover-line" style={{ left: `${left}%` }} />
              <span
                className="hover-dot"
                style={{ left: `${left}%`, top: `${(s.y(vals[h]) / H) * 100}%`, background: color }}
              />
              <span
                className="tooltip"
                style={{
                  left: `${left}%`,
                  transform: left > 60 ? "translateX(calc(-100% - 10px))" : "translateX(10px)",
                }}
              >
                <span className="tooltip-label">{labels[h]}</span>
                <span className="tooltip-value">
                  {fmt(vals[h])} <span style={{ color: dirColor(p) }}>{signedPct(p)}</span>
                </span>
              </span>
            </>
          );
        })()}
      <span
        className="chart-hit"
        onPointerDown={onMove}
        onPointerMove={onMove}
        onPointerLeave={(e) => e.pointerType === "mouse" && setHover(null)}
      />
    </>
  );
}

// ---------------------------------------------------------------- rates & commodities

function ExtraCell({ q }: { q: ExtraQuote }) {
  const pct = q.error ? null : pctChange(q);
  const price = q.error || q.price == null ? null : q.symbol === "^TNX" ? `${fmt(q.price, 3)}%` : fmt(q.price);
  return (
    <div className="extra">
      <span className="extra-key">
        <span className="sym">{q.name}</span>
        <span className="extra-label">{q.label}</span>
      </span>
      <span className="extra-price">{price ?? NA}</span>
      <span className="extra-foot">
        <span style={{ fontWeight: 600, color: dirColor(pct) }}>{pct == null ? "" : arrowPct(pct)}</span>
        <Spark
          className="spark spark-sm"
          levels={sparkLevels(
            q.history_5d.map((p) => p.close),
            8,
          )}
          color={pct == null || Math.abs(pct) < 0.005 ? "var(--na)" : pct < 0 ? "var(--down)" : "var(--up)"}
        />
      </span>
    </div>
  );
}
