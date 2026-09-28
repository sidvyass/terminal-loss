// Exchange sessions; mirrors ui.SESSIONS / session_status. Holidays are ignored.

interface Session {
  tz: string;
  open: number; // minutes after local midnight
  close: number;
  label: string;
}

export const SESSIONS: Record<string, Session> = {
  NYSE: { tz: "America/New_York", open: 9 * 60 + 30, close: 16 * 60, label: "ET" },
  BSE: { tz: "Asia/Kolkata", open: 9 * 60 + 15, close: 15 * 60 + 30, label: "IST" },
};

export function sessionStatus(exchange: string, now = new Date()): { open: boolean; time: string } {
  const { tz, open, close, label } = SESSIONS[exchange];
  const parts = Object.fromEntries(
    new Intl.DateTimeFormat("en-US", {
      timeZone: tz,
      weekday: "short",
      hour: "2-digit",
      minute: "2-digit",
      hourCycle: "h23",
    })
      .formatToParts(now)
      .map((p) => [p.type, p.value]),
  );
  const minutes = Number(parts.hour) * 60 + Number(parts.minute);
  const weekday = !["Sat", "Sun"].includes(parts.weekday);
  return { open: weekday && minutes >= open && minutes < close, time: `${parts.hour}:${parts.minute} ${label}` };
}

export function clock(epochSeconds: number): string {
  return new Date(epochSeconds * 1000).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" });
}
