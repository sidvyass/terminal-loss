"""Fetches snapshots from Yahoo / IMF / BIS and caches the latest one for API clients."""

import threading
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from market_cli.config import COUNTRIES, EXTRAS, MIN_REFRESH_SECONDS, TICKERS
from market_cli.data import Quote, fetch_quotes
from market_cli.macro import CountryStats, cache_checked_at, fetch_country_stats


@dataclass
class Snapshot:
    quotes: list[Quote]
    extras: list[Quote]
    countries: list[CountryStats]
    fx: dict[str, Quote]  # currency -> local currency per USD
    macro_fetched: float | None


def fetch() -> Snapshot:
    # Stocks, rates & commodities and FX rates all come from one Yahoo batch; split afterwards.
    fx_symbols = {f"FX {c['currency']}": c["fx"] for c in COUNTRIES.values() if c["fx"]}
    with ThreadPoolExecutor(max_workers=1) as pool:  # macro data (IMF/BIS) loads alongside the quotes
        macro = pool.submit(fetch_country_stats)
        quotes = fetch_quotes({**TICKERS, **EXTRAS, **fx_symbols})
        countries = macro.result()
    n_stocks, n_extras = len(TICKERS), len(EXTRAS)
    stocks = quotes[:n_stocks]
    extras = quotes[n_stocks : n_stocks + n_extras]
    fx = {q.name.removeprefix("FX "): q for q in quotes[n_stocks + n_extras :]}
    return Snapshot(stocks, extras, countries, fx, cache_checked_at())


class SnapshotCache:
    """Serves the latest snapshot; refetches when it is older than `max_age` seconds or on `force`.

    Concurrent callers share one fetch: they wait on the lock and then reuse the fresh result.
    """

    def __init__(self, fetcher: Callable[[], Snapshot] = fetch, max_age: float = MIN_REFRESH_SECONDS) -> None:
        self._fetcher = fetcher
        self._max_age = max_age
        self._lock = threading.Lock()
        self._snapshot: Snapshot | None = None
        self._fetched_at = 0.0
        self._fetches = 0  # bumped per fetch, so waiters can tell a fetch finished while they queued

    def get(self, force: bool = False) -> Snapshot:
        seen = self._fetches
        with self._lock:
            if self._snapshot is not None:
                # Another caller fetched while we waited: that counts as our refresh, even when forced.
                if self._fetches != seen:
                    return self._snapshot
                if not force and time.monotonic() - self._fetched_at < self._max_age:
                    return self._snapshot
            self._snapshot = self._fetcher()
            self._fetched_at = time.monotonic()
            self._fetches += 1
            return self._snapshot
