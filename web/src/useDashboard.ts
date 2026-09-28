// Dashboard state: view (tab, sorts, selection), the refresh countdown and the latest snapshot.

import { useCallback, useEffect, useRef, useState } from "react";
import { type Snapshot, fetchSnapshot } from "./api";
import { COUNTRY_SORTS, type CountrySort, QUOTE_SORTS, type QuoteSort, cycle, sortCountries } from "./sorting";

export type Tab = "markets" | "countries";

const REFRESH_SECONDS = 60;
const MIN_REFRESH_SECONDS = 15; // same floor as the CLI, to stay clear of Yahoo rate limits

// Optional URL settings: ?interval=30&tab=countries&spark=0
const params = new URLSearchParams(window.location.search);
export const SETTINGS = {
  interval: Math.max(MIN_REFRESH_SECONDS, Number(params.get("interval")) || REFRESH_SECONDS),
  startTab: (params.get("tab") === "countries" ? "countries" : "markets") as Tab,
  sparklines: params.get("spark") !== "0",
};

export function useDashboard() {
  const { interval } = SETTINGS;
  const [tab, setTab] = useState<Tab>(SETTINGS.startTab);
  const [sort, setSort] = useState<QuoteSort>("group");
  const [countrySort, setCountrySort] = useState<CountrySort>(COUNTRY_SORTS[0]);
  const [selected, setSelected] = useState("India");
  const [snapshot, setSnapshot] = useState<Snapshot | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [remaining, setRemaining] = useState(interval);
  const [refreshing, setRefreshing] = useState(false);
  const [now, setNow] = useState(() => new Date());
  const inFlight = useRef(false);

  const refresh = useCallback(
    async (force: boolean) => {
      if (inFlight.current) return; // ignore requests while a fetch is running
      inFlight.current = true;
      setRefreshing(true);
      try {
        setSnapshot(await fetchSnapshot(force));
        setError(null);
      } catch (e) {
        setError(e instanceof Error ? e.message : String(e)); // keep showing the last snapshot
      } finally {
        inFlight.current = false;
        setRefreshing(false);
        setRemaining(interval);
      }
    },
    [interval],
  );

  useEffect(() => {
    void refresh(false);
    const id = setInterval(() => {
      setNow(new Date());
      if (!inFlight.current) setRemaining((r) => r - 1);
    }, 1000);
    return () => clearInterval(id);
  }, [refresh]);

  useEffect(() => {
    if (remaining <= 0) void refresh(false);
  }, [remaining, refresh]);

  // Keys match cli.py: 1/2 and Tab switch tabs, s cycles the sort, up/down or k/j move the
  // country selection, r refreshes now. None of them refetch except r.
  const latest = useRef({ tab, countrySort, selected, snapshot });
  latest.current = { tab, countrySort, selected, snapshot };
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      const target = e.target as HTMLElement | null;
      if (target && /^(INPUT|TEXTAREA|SELECT)$/.test(target.tagName)) return;
      const cur = latest.current;
      const k = e.key;
      if (k === "1") setTab("markets");
      else if (k === "2") setTab("countries");
      else if (k === "Tab") {
        e.preventDefault();
        setTab(cur.tab === "markets" ? "countries" : "markets");
      } else if (k === "r" || k === "R") void refresh(true);
      else if (k === "s" || k === "S") {
        if (cur.tab === "markets") setSort((s) => cycle(QUOTE_SORTS.map(([key]) => key), s));
        else setCountrySort((s) => cycle(COUNTRY_SORTS, s));
      } else if (cur.tab === "countries" && ["ArrowUp", "ArrowDown", "k", "j"].includes(k)) {
        e.preventDefault();
        const names = sortCountries(cur.snapshot?.countries ?? [], cur.countrySort).map((c) => c.name);
        if (!names.length) return;
        const i = Math.max(0, names.indexOf(cur.selected));
        const next = Math.max(0, Math.min(names.length - 1, i + (k === "ArrowUp" || k === "k" ? -1 : 1)));
        setSelected(names[next]);
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [refresh]);

  return {
    tab, setTab, sort, setSort, countrySort, setCountrySort, selected, setSelected,
    snapshot, error, remaining, refreshing, interval, now,
    refreshNow: () => void refresh(true),
  };
}

export type Dashboard = ReturnType<typeof useDashboard>;
