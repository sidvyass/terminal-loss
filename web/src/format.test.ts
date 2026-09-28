import { describe, expect, it } from "vitest";
import {
  arrowPct,
  barHeight,
  compact,
  dirColor,
  fmt,
  fpct,
  niceStep,
  rangePos,
  signedChange,
  signedPct,
  sparkLevels,
  ticker,
} from "./format";

describe("number formatting", () => {
  it("formats with grouping and fixed digits", () => {
    expect(fmt(1234.5)).toBe("1,234.50");
    expect(fmt(0.1234, 3)).toBe("0.123");
  });

  it("compacts large values", () => {
    expect(compact(612.84)).toBe("612.84");
    expect(compact(82_612)).toBe("82.6k");
    expect(compact(-12_000)).toBe("-12.0k");
  });

  it("strips trailing zeros from percentages", () => {
    expect(fpct(3.875)).toBe("3.875%");
    expect(fpct(2.3)).toBe("2.3%");
    expect(fpct(5)).toBe("5%");
  });

  it("signs changes and treats tiny moves as zero", () => {
    expect(signedChange(1.5)).toBe("▲ 1.50");
    expect(signedChange(-1.5)).toBe("▼ 1.50");
    expect(signedChange(0.004)).toBe("0.00");
    expect(signedPct(2.25)).toBe("+2.25%");
    expect(signedPct(-2.25)).toBe("−2.25%");
    expect(signedPct(-0.001)).toBe("0.00%");
    expect(arrowPct(6.19)).toBe("▲ 6.19%");
  });

  it("picks direction colors", () => {
    expect(dirColor(null)).toBe("var(--dim)");
    expect(dirColor(0.001)).toBe("var(--dim)");
    expect(dirColor(1)).toBe("var(--up)");
    expect(dirColor(-1)).toBe("var(--down)");
  });
});

describe("rangePos", () => {
  it("clamps to 0-100", () => {
    expect(rangePos(5, 0, 10)).toBe(50);
    expect(rangePos(-5, 0, 10)).toBe(0);
    expect(rangePos(50, 0, 10)).toBe(100);
    expect(rangePos(3, 3, 3)).toBe(0);
  });
});

describe("niceStep", () => {
  it("rounds to 1, 2, 5 or 10 times a power of ten", () => {
    expect(niceStep(1.2)).toBe(1);
    expect(niceStep(2.4)).toBe(2);
    expect(niceStep(4)).toBe(5);
    expect(niceStep(8)).toBe(10);
    expect(niceStep(0.025)).toBeCloseTo(0.02);
    expect(niceStep(420)).toBe(500);
  });
});

describe("ticker", () => {
  it("drops index carets and the crypto USD suffix", () => {
    expect(ticker("^BSESN")).toBe("BSESN");
    expect(ticker("BTC-USD")).toBe("BTC");
    expect(ticker("NVDA")).toBe("NVDA");
  });
});

describe("sparkLevels", () => {
  it("handles empty, single and flat series", () => {
    expect(sparkLevels([], 5)).toEqual([]);
    expect(sparkLevels([4], 3)).toEqual([3, 3, 3]);
    expect(sparkLevels([2, 2, 2], 4)).toEqual([3, 3, 3, 3]);
  });

  it("scales min-max to 0-7", () => {
    expect(sparkLevels([0, 7], 2)).toEqual([0, 7]);
    expect(sparkLevels([10, 20, 30], 3)).toEqual([0, 4, 7]);
  });

  it("keeps the lowest bar visible", () => {
    expect(barHeight(0)).toBe(10);
    expect(barHeight(7)).toBe(100);
  });
});
