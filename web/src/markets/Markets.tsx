// Markets tab: breadth row, grouped stocks table, rates & commodities.

import { type CSSProperties, useEffect, useState } from "react";
import { type ExtraQuote, type StockQuote, change, pctChange } from "../api";
import {
  compact,
  dirColor,
  fmt,
  rangePos,
  signedChange,
  signedPct,
  sparkLevels,
  ticker,
} from "../format";
import { QUOTE_SORTS, type QuoteSort, sortQuotes } from "../sorting";
import { Spark } from "../Spark";
import { SETTINGS, type Dashboard } from "../useDashboard";

const HIGH_VOLUME = 1.5; // VOL ratio at or above this is highlighted
const ERROR_WIDTH = 14; // max length of an error message in the PRICE cell
const SPARK_MIN_WIDTH = 900; // below this viewport width the 5 DAYS column is hidden
const COLS = "64px minmax(110px,1.1fr) 100px 100px 72px minmax(190px,1.6fr) minmax(190px,1.6fr) 56px";

function useMinWidth(px: number): boolean {
  const query = `(min-width: ${px}px)`;
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches);
  useEffect(() => {
    const mq = window.matchMedia(query);
    const onChange = () => setMatches(mq.matches);
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, [query]);
  return matches;
}

export function Markets({ d, quotes, extras }: { d: Dashboard; quotes: StockQuote[]; extras: ExtraQuote[] }) {
  return (
    <>
      <Breadth quotes={quotes} />
      <section className="section">
        <div className="section-head">
          <h2>Stocks</h2>
          <span className="sort-control">
            <span className="kicker">Sort · S</span>
            <span className="seg">
              {QUOTE_SORTS.map(([key, label]) => (
                <button key={key} className={`seg-opt${d.sort === key ? " active" : ""}`} onClick={() => d.setSort(key)}>
                  {label}
                </button>
              ))}
            </span>
          </span>
        </div>
        <StocksTable quotes={quotes} sort={d.sort} />
      </section>
      <section className="section">
        <h2 className="section-title">Rates &amp; commodities</h2>
        <div className="cells extras">
          {extras.map((q) => (
            <ExtraCell key={q.symbol} q={q} />
          ))}
        </div>
      </section>
    </>
  );
}

function Breadth({ quotes }: { quotes: StockQuote[] }) {
  // Only quotes that moved count, as in the CLI.
  const moved = quotes.flatMap((q) => {
    const pct = q.error ? null : pctChange(q);
    return pct ? [{ q, pct }] : [];
  });
  const ups = moved.filter((m) => m.pct > 0).length;
  const best = moved.reduce<(typeof moved)[number] | null>((a, b) => (!a || b.pct > a.pct ? b : a), null);
  const worst = moved.reduce<(typeof moved)[number] | null>((a, b) => (!a || b.pct < a.pct ? b : a), null);
  return (
    <div className="breadth">
      <div className="breadth-cell">
        <span className="kicker">Breadth</span>
        <span className="big up">{ups} ▲</span>
        <span className="big down">{moved.length - ups} ▼</span>
      </div>
      {(
        [
          ["Best", best],
          ["Worst", worst],
        ] as const
      ).map(([label, m]) => (
        <div key={label} className="breadth-cell">
          <span className="kicker">{label}</span>
          {m ? (
            <>
              <span className="big sym">{ticker(m.q.symbol)}</span>
              <span style={{ fontWeight: 600, color: dirColor(m.pct) }}>{signedPct(m.pct)}</span>
            </>
          ) : (
            <span className="na">N/A</span>
          )}
        </div>
      ))}
    </div>
  );
}

function StocksTable({ quotes, sort }: { quotes: StockQuote[]; sort: QuoteSort }) {
  const showSpark = useMinWidth(SPARK_MIN_WIDTH) && SETTINGS.sparklines;
  const style = { "--cols": showSpark ? `${COLS} 96px` : COLS } as CSSProperties;

  // Grouped: labels in config (snapshot) order. Other sorts: one flat list.
  const sections: { label: string | null; rows: StockQuote[] }[] = [];
  if (sort === "group") {
    for (const q of quotes) {
      const label = q.group ?? "";
      const last = sections[sections.length - 1];
      if (last && last.label === label) last.rows.push(q);
      else sections.push({ label, rows: [q] });
    }
  } else {
    sections.push({ label: null, rows: sortQuotes(quotes, sort) });
  }

  return (
    <div className="scroller">
      <div className="stocks" style={style}>
        <div className="stocks-head">
          <span>Symbol</span>
          <span>Name</span>
          <span className="num">Price</span>
          <span className="num">Change</span>
          <span className="num">%</span>
          <span>Day range</span>
          <span>52-week range</span>
          <span className="num amber">Vol</span>
          {showSpark && <span className="num">5 days</span>}
        </div>
        {sections.map((s, i) => (
          <div key={s.label ?? i}>
            {s.label != null && <div className="group-label">{s.label}</div>}
            {s.rows.map((q) => (
              <StockRow key={q.symbol} q={q} showSpark={showSpark} />
            ))}
          </div>
        ))}
        <p className="caption">VOL = today's volume vs 3-month average, amber at 1.5× or more</p>
      </div>
    </div>
  );
}

const NA = <span className="na">N/A</span>;

function StockRow({ q, showSpark }: { q: StockQuote; showSpark: boolean }) {
  const chg = change(q);
  const pct = pctChange(q);
  if (q.error || q.price == null || chg == null || pct == null) {
    let message = `error: ${q.error ?? "no data"}`;
    if (message.length > ERROR_WIDTH) message = message.slice(0, ERROR_WIDTH - 1) + "…";
    return (
      <div className="stocks-row">
        <span className="sym">{ticker(q.symbol)}</span>
        <span className="name">{q.name}</span>
        <span className="num down" style={{ whiteSpace: "nowrap" }}>{message}</span>
        <span className="num">{NA}</span>
        <span className="num">{NA}</span>
        <span>{NA}</span>
        <span>{NA}</span>
        <span className="num">{NA}</span>
        {showSpark && <span className="num">{NA}</span>}
      </div>
    );
  }
  const color = dirColor(chg);
  return (
    <div className="stocks-row">
      <span className="sym">{ticker(q.symbol)}</span>
      <span className="name" title={q.name}>{q.name}</span>
      <span className="price">{fmt(q.price)}</span>
      <span className="num" style={{ color, fontWeight: 600, whiteSpace: "nowrap" }}>{signedChange(chg)}</span>
      <span className="num" style={{ color, fontWeight: 600 }}>{signedPct(pct)}</span>
      <RangeBar value={q.price} low={q.day_low} high={q.day_high} marker="var(--amber)" />
      <RangeBar value={q.price} low={q.year_low} high={q.year_high} marker="var(--blue)" />
      <span className="num">
        <Volume q={q} />
      </span>
      {showSpark && <Spark className="spark" levels={sparkLevels(q.history, 10)} color={chg < 0 ? "var(--down)" : "var(--up)"} />}
    </div>
  );
}

function RangeBar({ value, low, high, marker }: { value: number; low: number | null; high: number | null; marker: string }) {
  if (low == null || high == null) return NA;
  return (
    <span className="range">
      <span>{compact(low)}</span>
      <span className="range-track">
        <span className="range-mark" style={{ left: `calc(${rangePos(value, low, high)}% - 6px)`, background: marker }} />
      </span>
      <span>{compact(high)}</span>
    </span>
  );
}

function Volume({ q }: { q: StockQuote }) {
  if (!q.volume || !q.avg_volume) return <span className="vol na">N/A</span>; // indices report 0 volume
  const ratio = q.volume / q.avg_volume;
  return <span className={`vol${ratio >= HIGH_VOLUME ? " high" : ""}`}>{fmt(ratio, 1)}×</span>;
}

function ExtraCell({ q }: { q: ExtraQuote }) {
  const pct = q.error ? null : pctChange(q);
  const price = q.error || q.price == null ? null : q.symbol === "^TNX" ? `${fmt(q.price, 3)}%` : fmt(q.price);
  const arrow = pct == null ? "" : pct > 0 ? "▲ " : pct < 0 ? "▼ " : "";
  return (
    <div className="cell">
      <span className="cell-key">
        <span className="sym">{q.name}</span>
        <span className="sub">{q.label}</span>
      </span>
      <span className="cell-value">{price ?? NA}</span>
      <span className="extra-foot">
        <span style={{ fontWeight: 600, fontSize: 14, color: dirColor(pct) }}>
          {pct == null ? "" : `${arrow}${fmt(Math.abs(pct))}%`}
        </span>
        <Spark
          className="spark spark-sm"
          levels={sparkLevels(q.history, 8)}
          color={pct == null || pct === 0 ? "var(--na)" : pct < 0 ? "var(--down)" : "var(--up)"}
        />
      </span>
    </div>
  );
}
