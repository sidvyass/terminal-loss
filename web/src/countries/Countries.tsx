// Countries tab: sortable macro table and the selected country's 10-year trend.

import type { Country, Metric } from "../api";
import { METRICS } from "../api";
import { fmt, fpct, sparkLevels } from "../format";
import { type CountrySort, sortCountries } from "../sorting";
import { Spark } from "../Spark";
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
    <>
      <section className="section">
        <div className="section-head">
          <h2>Countries</h2>
          <span className="hint">Click a column to sort · click a row or use ↑↓ to select</span>
        </div>
        <CountryTable d={d} countries={countries} />
      </section>
      {selected && <TrendPanel country={selected} />}
    </>
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
    <div className="scroller">
      <div className="countries">
        <div className="countries-head">
          {heads.map(([key, label]) => (
            <button
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
          <div
            key={c.name}
            className={`country-row${c.name === d.selected ? " selected" : ""}`}
            onClick={() => d.setSelected(c.name)}
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
                    <span style={{ width: `${width}%`, background: active ? "var(--amber)" : countryColor(c.name) }} />
                  </span>
                </span>
              );
            })}
          </div>
        ))}
        <p className="caption">Bars scale to the highest value in each column · * cached · N/A = no IMF series</p>
      </div>
    </div>
  );
}

function TrendPanel({ country }: { country: Country }) {
  const color = countryColor(country.name);
  return (
    <section className="section">
      <div className="section-head">
        <h2>
          {country.name} <span className="trend-suffix">· 10-year trend</span>
        </h2>
        <span className="hint">
          {HISTORY_START} → {THIS_YEAR} · same IMF DataMapper call
        </span>
      </div>
      <div className="cells trend" style={{ borderTopColor: color }}>
        {METRICS.map((m) => {
          const stat = country.stats[m];
          const values = (country.history[m] ?? []).map(([, v]) => v);
          // BIS policy rates have no history in this call, so no spark.
          const levels = m !== "interest_rate" && values.length > 1 ? sparkLevels(values, 11) : [];
          let note = "IMF WEO";
          if (!stat) note = "no IMF series";
          else if (stat.stale) note = "cached";
          else if (m === "interest_rate") note = `${country.central_bank ?? "central bank"} · ${stat.period}`;
          return (
            <div key={m} className="cell">
              <span className="sub">{METRIC_LABELS[m][1]}</span>
              <span className="cell-value">{stat ? fpct(stat.value) : <span className="na">N/A</span>}</span>
              <Spark className="spark trend-spark" levels={stat ? levels : []} color={color} />
              <span className={stat?.stale ? "sub stale" : "sub"}>{note}</span>
            </div>
          );
        })}
      </div>
    </section>
  );
}
