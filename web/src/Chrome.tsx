// Page frame shared by both tabs: nav bar, status strip and footer.

import { THIS_YEAR } from "./countries/Countries";
import { clock, sessionStatus } from "./sessions";
import type { Dashboard, Tab } from "./useDashboard";

const TABS: [Tab, string, string][] = [
  ["markets", "1", "Markets"],
  ["countries", "2", "Countries"],
];

export function Nav({ d }: { d: Dashboard }) {
  return (
    <nav className="nav">
      <span className="nav-brand">market-cli</span>
      {TABS.map(([tab, key, label]) => (
        <button key={tab} className={`tab${d.tab === tab ? " active" : ""}`} onClick={() => d.setTab(tab)}>
          <span className="chip">{key}</span>
          {label}
        </button>
      ))}
      <span className="nav-actions">
        <button className="btn" onClick={d.refreshNow}>
          <span>Refresh now</span>
          <span className="chip">R</span>
        </button>
      </span>
    </nav>
  );
}

interface Cell {
  kicker: string;
  value: string;
  sub: string;
  dot?: string; // square status dot color
}

function marketCells(now: Date): Cell[] {
  return (["NYSE", "BSE"] as const).map((exchange) => {
    const s = sessionStatus(exchange, now);
    return { kicker: exchange, value: s.open ? "Open" : "Closed", dot: s.open ? "var(--up)" : "var(--amber)", sub: s.time };
  });
}

function countryCells(macroFetchedAt: number | null): Cell[] {
  return [
    { kicker: "Sources", value: `IMF WEO ${THIS_YEAR}`, sub: `Estimates for ${THIS_YEAR} · policy rates BIS · FX live` },
    {
      kicker: "Macro cache",
      value: macroFetchedAt ? `Fetched ${clock(macroFetchedAt)}` : "Not fetched",
      sub: "Cached for 12h",
    },
  ];
}

export function StatusStrip({ d }: { d: Dashboard }) {
  const cells = d.tab === "markets" ? marketCells(d.now) : countryCells(d.snapshot?.macro_fetched_at ?? null);
  const pct = d.refreshing ? 0 : (Math.max(0, d.remaining) / d.interval) * 100;
  return (
    <div className="status">
      {cells.map((c) => (
        <div key={c.kicker} className="status-cell">
          <span className="kicker">{c.kicker}</span>
          <span className="status-value">
            {c.dot && <span className="dot" style={{ background: c.dot }} />}
            {c.value}
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
    ["S", "sort"],
    ["R", "refresh now"],
  ],
  countries: [
    ["1 2", "tabs"],
    ["↑↓", "select country"],
    ["S", "sort column"],
    ["R", "refresh now"],
  ],
};

export function Footer({ tab }: { tab: Tab }) {
  return (
    <footer className="footer">
      <span>{tab === "markets" ? "Yahoo Finance · 5-day hourly closes" : "IMF WEO (year shown) · policy rates: BIS"}</span>
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
