import { describe, expect, it } from "vitest";
import type { Country, StockQuote } from "./api";
import { cycle, sortCountries, sortQuotes } from "./sorting";

function quote(symbol: string, name: string, price: number | null, prevClose: number | null, error?: string) {
  return { symbol, name, price, prev_close: prevClose, error: error ?? null, group: "STOCKS" } as StockQuote;
}

function country(name: string, gdp?: number): Country {
  return {
    name,
    stats: gdp == null ? {} : { gdp_growth: { value: gdp, period: "2026", stale: false } },
  } as Country;
}

describe("cycle", () => {
  it("wraps around", () => {
    expect(cycle(["a", "b", "c"], "a")).toBe("b");
    expect(cycle(["a", "b", "c"], "c")).toBe("a");
  });
});

describe("sortQuotes", () => {
  const quotes = [
    quote("AAA", "beta", 110, 100), // +10%
    quote("BBB", "Alpha", 95, 100), // -5%
    quote("CCC", "gamma", null, null, "no data"),
    quote("DDD", "delta", 102, 100), // +2%
  ];

  it("keeps config order for group", () => {
    expect(sortQuotes(quotes, "group")).toBe(quotes);
  });

  it("sorts by % change descending with errors last", () => {
    expect(sortQuotes(quotes, "pct").map((q) => q.symbol)).toEqual(["AAA", "DDD", "BBB", "CCC"]);
  });

  it("sorts by name case-insensitively without mutating the input", () => {
    expect(sortQuotes(quotes, "name").map((q) => q.name)).toEqual(["Alpha", "beta", "delta", "gamma"]);
    expect(quotes[0].symbol).toBe("AAA");
  });
});

describe("sortCountries", () => {
  const countries = [country("India", 6.5), country("Brazil"), country("Japan", 0.6), country("China", 4.8)];

  it("sorts by metric descending with missing values last", () => {
    expect(sortCountries(countries, "gdp_growth").map((c) => c.name)).toEqual(["India", "China", "Japan", "Brazil"]);
  });

  it("sorts by name", () => {
    expect(sortCountries(countries, "name").map((c) => c.name)).toEqual(["Brazil", "China", "India", "Japan"]);
  });
});
