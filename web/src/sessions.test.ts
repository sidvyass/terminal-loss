import { describe, expect, it } from "vitest";
import { sessionStatus } from "./sessions";

describe("sessionStatus", () => {
  it("is open during NYSE hours on a weekday", () => {
    // Mon 2026-09-28 10:00 EDT
    expect(sessionStatus("NYSE", new Date("2026-09-28T14:00:00Z"))).toEqual({ open: true, time: "10:00 ET" });
  });

  it("is closed before the open and at the close", () => {
    expect(sessionStatus("NYSE", new Date("2026-09-28T13:29:00Z")).open).toBe(false); // 09:29 EDT
    expect(sessionStatus("NYSE", new Date("2026-09-28T20:00:00Z")).open).toBe(false); // 16:00 EDT
  });

  it("is closed at weekends", () => {
    expect(sessionStatus("NYSE", new Date("2026-09-26T14:00:00Z")).open).toBe(false); // Saturday
  });

  it("uses the exchange's own time zone", () => {
    // 04:00 UTC = 09:30 IST
    expect(sessionStatus("BSE", new Date("2026-09-28T04:00:00Z"))).toEqual({ open: true, time: "09:30 IST" });
  });
});
