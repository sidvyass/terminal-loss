// Countries tab: sortable macro table and, beside it, the selected country's 10-year trend charts.
// Phones swap the wide table for a country chip strip above the trend and a ranked list below it.

import { type RefObject, useRef } from "react";
import type { Country, Metric } from "../api";
import { METRICS } from "../api";
import { fmt, fpct } from "../format";
import { revealOnPhone } from "../mobile";
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
const nameColor = (name: string) => (name === "India" ? "var(--violet)" : "var(--text)");

/** "INR ₹88.72", or just "USD" for the base currency. */
function fxLabel(c: Country): string {
  if (c.currency === "USD") return "USD";
  return `${c.currency} ${c.fx_rate == null ? "N/A" : `${c.currency_symbol}${fmt(c.fx_rate)}`}`;
}

export function Countries({ d, countries }: { d: Dashboard; countries: Country[] }) {
  const selected = countries.find((c) => c.name === d.selected) ?? countries[0];
  const trendRef = useRef<HTMLElement>(null);
  return (
    <div className="countries-layout">
      <section className="desk-only">
        <div className="panel-head">
          <h2>Countries</h2>
          <span className="hint">Click a column to sort · ↑↓ to select</span>
        </div>
        <CountryTable d={d} countries={countries} />
      </section>
      <div className="country-chips phone-only">
        {countries.map((c) => (
          <button
            type="button"
            key={c.name}
            className={`country-chip${c.name === selected?.name ? " active" : ""}`}
            style={c.name === selected?.name ? undefined : { color: nameColor(c.name) }}
            onClick={() => d.setSelected(c.name)}
          >
            {c.name}
          </button>
        ))}
      </div>
      {selected && <TrendPanel country={selected} panelRef={trendRef} />}
      <CompareList d={d} countries={countries} trendRef={trendRef} />
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
              <span className="country-name" style={{ color: nameColor(c.name) }}>
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

/** Phones: one metric at a time, countries ranked high → low with bars. */
function CompareList({
  d,
  countries,
  trendRef,
}: {
  d: Dashboard;
  countries: Country[];
  trendRef: RefObject<HTMLElement | null>;
}) {
  const sort: Metric = d.countrySort === "name" ? "gdp_growth" : d.countrySort;
  const max = Math.max(0, ...countries.map((c) => Math.abs(c.stats[sort]?.value ?? 0)));
  const select = (name: string) => {
    d.setSelected(name);
    revealOnPhone(trendRef.current);
  };
  return (
    <section className="compare phone-only">
      <div className="panel-head">
        <h2>Compare</h2>
        <span className="hint">Ranked high → low</span>
      </div>
      <div className="compare-metrics">
        {METRICS.map((m) => (
          <button
            type="button"
            key={m}
            className={`seg-opt${m === sort ? " active" : ""}`}
            onClick={() => d.setCountrySort(m)}
          >
            {METRIC_LABELS[m][0]}
          </button>
        ))}
      </div>
      {sortCountries(countries, sort).map((c, i) => {
        const stat = c.stats[sort];
        const width = stat && max > 0 ? Math.min(Math.abs(stat.value) / max, 1) * 100 : 0;
        return (
          // biome-ignore lint/a11y/useSemanticElements: a grid row; a <button> would bring its own box styles
          <div
            key={c.name}
            className={`compare-row${c.name === d.selected ? " selected" : ""}`}
            role="button"
            tabIndex={0}
            onClick={() => select(c.name)}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                e.preventDefault();
                select(c.name);
              }
            }}
          >
            <span className="dim">{i + 1}</span>
            <span className="compare-name">
              <span className="country-name" style={{ color: nameColor(c.name) }}>
                {c.name}
              </span>
              <span className="sub">{fxLabel(c)}</span>
            </span>
            <span className="compare-value">
              {stat ? fpct(stat.value) : <span className="na">N/A</span>}
              {stat?.stale && <span className="star">*</span>}
            </span>
            <span className="metric-bar">
              <span style={{ width: `${width}%`, background: "var(--amber)" }} />
            </span>
          </div>
        );
      })}
      <p className="caption">Bars scale to the highest value · * cached · tap a country to see its trend</p>
    </section>
  );
}

function TrendPanel({ country, panelRef }: { country: Country; panelRef: RefObject<HTMLElement | null> }) {
  const color = countryColor(country.name);
  return (
    <aside className="trend-panel" style={{ borderTopColor: color }} ref={panelRef}>
      <div className="trend-head">
        <span className="trend-title">
          <span style={{ color }}>{country.name}</span> <span className="trend-suffix">· 10-year trend</span>
        </span>
        <span className="hint">
          {/* Phones hide the table that shows the currency, so it moves here. */}
          <span className="phone-only">
            {country.currency === "USD" ? "USD · base currency" : `${fxLabel(country)} per $`} ·{" "}
          </span>
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
