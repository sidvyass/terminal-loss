// Page frame shared by both tabs: nav bar, status strip and footer.

import { pctChange, type StockQuote } from "./api";
import { THIS_YEAR } from "./countries/Countries";
import { dirColor, signedPct, ticker } from "./format";
import { clock, sessionStatus } from "./sessions";
import type { Dashboard, Tab } from "./useDashboard";

const TABS: [Tab, string, string][] = [
  ["markets", "1", "Markets"],
  ["countries", "2", "Countries"],
];

export function Nav({ d }: { d: Dashboard }) {
  return (
    <nav className="nav">
      <span className="nav-brand">Terminal Loss</span>
      {TABS.map(([tab, key, label]) => (
        <button
          type="button"
          key={tab}
          className={`tab${d.tab === tab ? " active" : ""}`}
          onClick={() => d.setTab(tab)}
        >
          <span className="chip">{key}</span>
          {label}
        </button>
      ))}
      <span className="nav-actions">
        <button type="button" className="btn" onClick={d.refreshNow} aria-label="Refresh now">
          <span className="btn-label">Refresh now</span>
          <span className="btn-icon" aria-hidden="true">
            ↻
          </span>
          <span className="chip">R</span>
        </button>
      </span>
    </nav>
  );
}

interface Cell {
  kicker: string;
  value: string;
  color?: string;
  value2?: string; // second value in another color, e.g. "3 ▼" after "7 ▲"
  color2?: string;
  sub: string;
  dot?: string; // square status dot color
}

function marketCells(now: Date, quotes: StockQuote[]): Cell[] {
  const sessions = (["NYSE", "BSE"] as const).map((exchange): Cell => {
    const s = sessionStatus(exchange, now);
    return {
      kicker: exchange,
      value: s.open ? "Open" : "Closed",
      dot: s.open ? "var(--up)" : "var(--amber)",
      sub: s.time,
    };
  });
  // Only quotes that moved count, as in the CLI.
  const moved = quotes.flatMap((q) => {
    const pct = q.error ? null : pctChange(q);
    return pct ? [{ q, pct }] : [];
  });
  const ups = moved.filter((m) => m.pct > 0).length;
  const pick = (label: string, better: (a: number, b: number) => boolean): Cell => {
    const m = moved.reduce<(typeof moved)[number] | null>((a, b) => (!a || better(b.pct, a.pct) ? b : a), null);
    return m
      ? {
          kicker: label,
          value: ticker(m.q.symbol),
          color: "var(--blue)",
          value2: signedPct(m.pct),
          color2: dirColor(m.pct),
          sub: m.q.name,
        }
      : { kicker: label, value: "N/A", color: "var(--na)", sub: "No moves yet" };
  };
  return [
    ...sessions,
    {
      kicker: "Breadth",
      value: `${ups} ▲`,
      color: "var(--up)",
      value2: `${moved.length - ups} ▼`,
      color2: "var(--down)",
      sub: `${quotes.length} symbols`,
    },
    pick("Best", (a, b) => a > b),
    pick("Worst", (a, b) => a < b),
  ];
}

function countryCells(macroFetchedAt: number | null): Cell[] {
  return [
    {
      kicker: "Sources",
      value: `IMF WEO ${THIS_YEAR}`,
      sub: `Estimates for ${THIS_YEAR} · policy rates BIS · FX live`,
    },
    {
      kicker: "Macro cache",
      value: macroFetchedAt ? `Fetched ${clock(macroFetchedAt)}` : "Not fetched",
      sub: "Cached for 12h",
    },
  ];
}

export function StatusStrip({ d }: { d: Dashboard }) {
  const cells =
    d.tab === "markets"
      ? marketCells(d.now, d.snapshot?.quotes ?? [])
      : countryCells(d.snapshot?.macro_fetched_at ?? null);
  const pct = d.refreshing ? 0 : (Math.max(0, d.remaining) / d.interval) * 100;
  return (
    <div className="status">
      {cells.map((c) => (
        <div key={c.kicker} className="status-cell">
          <span className="kicker">{c.kicker}</span>
          <span className="status-value">
            {c.dot && <span className="dot" style={{ background: c.dot }} />}
            <span style={{ color: c.color }}>{c.value}</span>
            {c.value2 && <span style={{ color: c.color2 }}>{c.value2}</span>}
          </span>
          <span className="sub">{c.sub}</span>
        </div>
      ))}
      <div className="status-cell">
        <span className="kicker">Next refresh</span>
        <span className="status-value">{d.refreshing ? "Refreshing…" : `${Math.max(0, d.remaining)}s`}</span>
        {d.error && !d.refreshing && <span className="sub down">Last refresh failed · {d.error}</span>}
        <span className="progress">
          <span style={{ width: `${pct}%` }} />
        </span>
      </div>
    </div>
  );
}

const HINTS: Record<Tab, [string, string][]> = {
  markets: [
    ["1 2", "tabs"],
    ["↑↓", "select"],
    ["←→", "range"],
    ["S", "sort"],
    ["R", "refresh"],
  ],
  countries: [
    ["1 2", "tabs"],
    ["↑↓", "select country"],
    ["S", "sort column"],
    ["R", "refresh"],
  ],
};

export function Footer({ tab }: { tab: Tab }) {
  return (
    <footer className="footer">
      <span>
        {tab === "markets" ? "Yahoo Finance · 5-day hourly closes" : "IMF WEO (year shown) · policy rates: BIS"}
      </span>
      <span className="hints">
        {HINTS[tab].map(([key, label]) => (
          <span key={key}>
            <span className="hint-key">{key}</span>
            {label}
          </span>
        ))}
      </span>
    </footer>
  );
}
