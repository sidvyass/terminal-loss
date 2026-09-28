import { describe, expect, it } from "vitest";
import type { Point } from "../api";
import { buildSeries, H, scale, W } from "./series";

const NY = "America/New_York";

function points(times: string[], start = 100): Point[] {
  return times.map((t, i) => ({ t, close: start + i }));
}

describe("buildSeries", () => {
  it("labels 1D points in exchange time and measures against the previous close", () => {
    const pts = points(["2026-09-28T13:30:00Z", "2026-09-28T13:35:00Z", "2026-09-28T13:40:00Z"]);
    const s = buildSeries(pts, "1D", 99, NY);
    expect(s.vals).toEqual([100, 101, 102]);
    expect(s.labels).toEqual(["09:30", "09:35", "09:40"]);
    expect(s.base).toBe(99);
    expect(s.ticks[0]).toEqual({ i: 0, label: "09:30" });
  });

  it("falls back to the first value as the base without a previous close", () => {
    const s = buildSeries(points(["2026-09-28T13:30:00Z", "2026-09-28T13:35:00Z"]), "1D", null, NY);
    expect(s.base).toBe(100);
  });

  it("puts one weekday tick per day for 5D", () => {
    const pts = points([
      "2026-09-24T14:00:00Z",
      "2026-09-24T15:00:00Z",
      "2026-09-24T16:00:00Z",
      "2026-09-25T14:00:00Z",
      "2026-09-25T15:00:00Z",
      "2026-09-25T16:00:00Z",
    ]);
    const s = buildSeries(pts, "5D", null, NY);
    expect(s.ticks.map((t) => t.label)).toEqual(["Thu", "Fri"]);
    expect(s.labels[0]).toBe("Thu 10:00");
  });

  it("labels 1Y points with the year", () => {
    const s = buildSeries(points(["2025-10-01T20:00:00Z", "2025-11-03T20:00:00Z"]), "1Y", null, NY);
    expect(s.labels).toEqual(["Oct 1, 2025", "Nov 3, 2025"]);
  });
});

describe("scale", () => {
  it("maps the domain into the SVG box with padding", () => {
    const s = scale([10, 20], 10);
    expect(s.x(0)).toBe(0);
    expect(s.x(1)).toBe(W);
    expect(s.y(10)).toBeLessThan(H);
    expect(s.y(20)).toBeGreaterThan(0);
    expect(s.line.startsWith("M0.0 ")).toBe(true);
    expect(s.area.endsWith("Z")).toBe(true);
    expect(s.yTicks.length).toBeGreaterThan(0);
  });

  it("centres a single point and survives a flat series", () => {
    const s = scale([5], 5);
    expect(s.x(0)).toBe(W / 2);
    expect(Number.isFinite(s.y(5))).toBe(true);
  });
});
