// Countries tab: sortable macro table and, beside it, the selected country's 10-year trend charts.

import type { Country, Metric } from "../api";
import { METRICS } from "../api";
import { fmt, fpct } from "../format";
import { type CountrySort, sortCountries } from "../sorting";
import type { Dashboard } from "../useDashboard";

export const THIS_YEAR = new Date().getFullYear();
export const HISTORY_START = THIS_YEAR - 10; // macro.HISTORY_YEARS

// metric -> (table header, trend label); mirrors ui.COUNTRY_METRICS
const METRIC_LABELS: Record<Metric, [string, string]> = {
  gdp_growth: ["GDP growth", "GDP growth"],
  unemployment: ["Unemployment", "Unemployment"],
  inflation: ["Inflation", "Inflation"],
  interest_rate: ["Policy rate", "Policy rate"],
  debt_to_gdp: ["Debt / GDP", "Gov. debt / GDP"],
};

const countryColor = (name: string) => (name === "India" ? "var(--violet)" : "var(--blue)");

export function Countries({ d, countries }: { d: Dashboard; countries: Country[] }) {
  const selected = countries.find((c) => c.name === d.selected) ?? countries[0];
  return (
    <div className="countries-layout">
      <section>
        <div className="panel-head">
          <h2>Countries</h2>
          <span className="hint">Click a column to sort · ↑↓ to select</span>
        </div>
        <CountryTable d={d} countries={countries} />
      </section>
      {selected && <TrendPanel country={selected} />}
    </div>
  );
}

function CountryTable({ d, countries }: { d: Dashboard; countries: Country[] }) {
  const sort = d.countrySort;
  // Bars scale to the highest absolute value in each column.
  const maxes = Object.fromEntries(
    METRICS.map((m) => [m, Math.max(0, ...countries.map((c) => Math.abs(c.stats[m]?.value ?? 0)))]),
  ) as Record<Metric, number>;
  const heads: [CountrySort | null, string][] = [
    ["name", "Country"],
    [null, "CCY · per $"],
    ...METRICS.map((m): [CountrySort, string] => [m, METRIC_LABELS[m][0]]),
  ];

  return (
    <>
      <div className="scroller">
        <div className="countries">
          <div className="countries-head">
            {heads.map(([key, label]) => (
              <button
                type="button"
                key={label}
                className={`col-head${key === sort ? " active" : ""}${key ? "" : " static"}`}
                onClick={() => key && d.setCountrySort(key)}
                tabIndex={key ? 0 : -1}
              >
                {label}
                {key === sort && <span>▼</span>}
              </button>
            ))}
          </div>
          {sortCountries(countries, sort).map((c) => (
            // biome-ignore lint/a11y/useSemanticElements: a grid row; a <button> would bring its own box styles
            <div
              key={c.name}
              className={`country-row${c.name === d.selected ? " selected" : ""}`}
              role="button"
              tabIndex={0}
              onClick={() => d.setSelected(c.name)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  e.preventDefault();
                  d.setSelected(c.name);
                }
              }}
            >
              <span className="country-name" style={{ color: c.name === "India" ? "var(--violet)" : "var(--text)" }}>
                {c.name}
              </span>
              <span className="ccy">
                <span style={{ fontWeight: 600 }}>{c.currency}</span>
                <span className="dim">{c.fx_rate == null ? "N/A" : `${c.currency_symbol}${fmt(c.fx_rate)}`}</span>
              </span>
              {METRICS.map((m) => {
                const stat = c.stats[m];
                const active = m === sort;
                if (!stat) {
                  return (
                    <span key={m} className="metric">
                      <span className="na">N/A</span>
                    </span>
                  );
                }
                const width = maxes[m] > 0 ? Math.min(Math.abs(stat.value) / maxes[m], 1) * 100 : 0;
                return (
                  <span key={m} className="metric">
                    <span style={{ fontWeight: active ? 800 : 400 }}>{fpct(stat.value)}</span>
                    <span className="star">{stat.stale ? "*" : ""}</span>
                    <span className="metric-bar">
                      <span
                        style={{ width: `${width}%`, background: active ? "var(--amber)" : countryColor(c.name) }}
                      />
                    </span>
                  </span>
                );
              })}
            </div>
          ))}
        </div>
      </div>
      <p className="caption">Bars scale to the highest value in each column · * cached · N/A = no IMF series</p>
    </>
  );
}

function TrendPanel({ country }: { country: Country }) {
  const color = countryColor(country.name);
  return (
    <aside className="trend-panel" style={{ borderTopColor: color }}>
      <div className="trend-head">
        <span className="trend-title">
          <span style={{ color }}>{country.name}</span> <span className="trend-suffix">· 10-year trend</span>
        </span>
        <span className="hint">
          {HISTORY_START} → {THIS_YEAR} · IMF DataMapper
        </span>
      </div>
      <div className="trend">
        {METRICS.map((m) => {
          const stat = country.stats[m];
          let note = `IMF WEO · ${THIS_YEAR} is an estimate`;
          if (!stat) note = "no IMF series";
          else if (stat.stale) note = "cached";
          // BIS policy rates have no history in this call, so no chart.
          else if (m === "interest_rate")
            note = `${country.central_bank ?? "Central bank"} · ${stat.period} · BIS returns the latest rate only, no history`;
          const points = m === "interest_rate" || !stat ? [] : (country.history[m] ?? []);
          return (
            <div key={m} className="trend-cell">
              <span className="trend-top">
                <span className="kicker">{METRIC_LABELS[m][1]}</span>
                <span className="trend-value">{stat ? fpct(stat.value) : <span className="na">N/A</span>}</span>
              </span>
              {points.length > 1 && <TrendChart points={points} color={color} />}
              <span className={stat?.stale ? "sub stale" : "sub"}>{note}</span>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

/** 10-year line: x by year from HISTORY_START to THIS_YEAR, y min..max with a dashed zero line. */
function TrendChart({ points, color }: { points: [number, number][]; color: string }) {
  const vals = points.map(([, v]) => v);
  let lo = Math.min(...vals);
  let hi = Math.max(...vals);
  if (hi === lo) {
    hi += 1;
    lo -= 1;
  }
  const x = (year: number) => ((year - HISTORY_START) / (THIS_YEAR - HISTORY_START)) * 100; // percent
  const y = (v: number) => ((hi - v) / (hi - lo)) * 100; // percent
  const line = points.map(([yr, v], i) => `${i ? "L" : "M"}${(x(yr) * 3).toFixed(1)} ${y(v).toFixed(1)}`).join("");
  const [lastYear, lastVal] = points[points.length - 1];
  return (
    <div className="trend-chart">
      <span className="trend-rule" style={{ top: 0 }}>
        <span className="trend-y" style={{ transform: "translateY(-50%)" }}>
          {fpct(hi)}
        </span>
      </span>
      <span className="trend-rule" style={{ top: "100%" }}>
        <span className="trend-y" style={{ transform: "translateY(-50%)" }}>
          {fpct(lo)}
        </span>
      </span>
      {lo < 0 && hi > 0 && <span className="base-line" style={{ top: `${y(0)}%` }} />}
      <svg viewBox="0 0 300 100" preserveAspectRatio="none" aria-hidden="true">
        <path d={line} vectorEffect="non-scaling-stroke" style={{ fill: "none", stroke: color, strokeWidth: 2 }} />
      </svg>
      <span className="trend-dot" style={{ left: `${x(lastYear)}%`, top: `${y(lastVal)}%`, background: color }} />
      <span className="trend-x" style={{ left: 0 }}>
        {HISTORY_START}
      </span>
      <span className="trend-x" style={{ left: "50%", transform: "translateX(-50%)" }}>
        {(HISTORY_START + THIS_YEAR) / 2}
      </span>
      <span className="trend-x" style={{ right: 0 }}>
        {THIS_YEAR}
      </span>
    </div>
  );
}
