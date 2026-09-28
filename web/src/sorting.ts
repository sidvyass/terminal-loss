// Sort orders; mirrors ui.sort_quotes / ui.sort_countries and the `s` cycle order in cli.py.

import { type Country, type Metric, METRICS, type StockQuote, pctChange } from "./api";

export type QuoteSort = "group" | "pct" | "name";
export const QUOTE_SORTS: [QuoteSort, string][] = [
  ["group", "group"],
  ["pct", "% change"],
  ["name", "name"],
];

export type CountrySort = Metric | "name";
export const COUNTRY_SORTS: CountrySort[] = [...METRICS, "name"];

export function cycle<T>(options: T[], current: T): T {
  return options[(options.indexOf(current) + 1) % options.length];
}

export function sortQuotes(quotes: StockQuote[], sort: QuoteSort): StockQuote[] {
  if (sort === "pct") {
    // Descending; errors / missing last.
    const key = (q: StockQuote) => (q.error ? null : pctChange(q));
    return [...quotes].sort((a, b) => {
      const x = key(a);
      const y = key(b);
      if (x == null || y == null) return (x == null ? 1 : 0) - (y == null ? 1 : 0);
      return y - x;
    });
  }
  if (sort === "name") return [...quotes].sort((a, b) => a.name.toLowerCase().localeCompare(b.name.toLowerCase()));
  return quotes; // "group": config order, which is grouped
}

export function sortCountries(countries: Country[], sort: CountrySort): Country[] {
  if (sort === "name") return [...countries].sort((a, b) => a.name.localeCompare(b.name));
  // Descending by value; countries with no value go last.
  return [...countries].sort((a, b) => {
    const x = a.stats[sort]?.value;
    const y = b.stats[sort]?.value;
    if (x == null || y == null) return (x == null ? 1 : 0) - (y == null ? 1 : 0);
    return y - x;
  });
}
