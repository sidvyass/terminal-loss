import threading
import time

import pytest
from conftest import make_snapshot

from terminal_loss.api import service
from terminal_loss.api.service import HistoryCache, Snapshot, SnapshotCache
from terminal_loss.config import EXTRAS, TICKERS
from terminal_loss.data import Quote


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> FakeClock:
    fake = FakeClock()
    monkeypatch.setattr(service.time, "monotonic", fake)
    return fake


def test_snapshot_cache_expires_after_max_age(clock: FakeClock) -> None:
    calls = []
    cache = SnapshotCache(lambda: calls.append(1) or make_snapshot(), max_age=15, min_force_age=5)
    cache.get()
    clock.now += 14
    cache.get()
    assert len(calls) == 1
    clock.now += 2
    cache.get()
    assert len(calls) == 2


def test_snapshot_cache_force_respects_floor(clock: FakeClock) -> None:
    calls = []
    cache = SnapshotCache(lambda: calls.append(1) or make_snapshot(), max_age=60, min_force_age=5)
    cache.get()
    clock.now += 4
    cache.get(force=True)
    assert len(calls) == 1
    clock.now += 2
    cache.get(force=True)
    assert len(calls) == 2


def test_snapshot_cache_serves_stale_on_failure(clock: FakeClock) -> None:
    results: list[Snapshot | Exception] = [make_snapshot(), RuntimeError("yahoo down")]

    def fetcher() -> Snapshot:
        r = results.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    cache = SnapshotCache(fetcher, max_age=15)
    first = cache.get()
    clock.now += 20
    assert cache.get() is first  # failure: the previous snapshot is kept
    clock.now += 1
    assert cache.get() is first  # ...and not retried until it expires again
    assert results == []


def test_snapshot_cache_raises_without_previous_snapshot() -> None:
    def fetcher() -> Snapshot:
        raise RuntimeError("yahoo down")

    with pytest.raises(RuntimeError):
        SnapshotCache(fetcher).get()


def test_snapshot_cache_shares_one_fetch_between_concurrent_callers() -> None:
    calls = []
    started = threading.Event()

    def fetcher() -> Snapshot:
        calls.append(1)
        started.set()
        time.sleep(0.2)
        return make_snapshot()

    cache = SnapshotCache(fetcher, max_age=60)
    first = threading.Thread(target=cache.get)
    first.start()
    started.wait()
    others = [threading.Thread(target=cache.get, kwargs={"force": True}) for _ in range(5)]
    for t in others:
        t.start()
    for t in [first, *others]:
        t.join()
    assert len(calls) == 1


def test_history_cache_ttl_per_range(clock: FakeClock) -> None:
    calls = []

    def fetcher(symbol: str, range_: str) -> list[tuple[str, float]]:
        calls.append((symbol, range_))
        return [("t", 1.0)]

    cache = HistoryCache(fetcher)
    cache.get("NVDA", "1D")
    cache.get("NVDA", "1Y")
    clock.now += 61
    cache.get("NVDA", "1D")  # 1D expires after a minute
    cache.get("NVDA", "1Y")  # 1Y is good for an hour
    assert calls == [("NVDA", "1D"), ("NVDA", "1Y"), ("NVDA", "1D")]


def test_history_cache_does_not_cache_failures() -> None:
    calls = []

    def fetcher(symbol: str, range_: str) -> list[tuple[str, float]]:
        calls.append(1)
        raise RuntimeError("boom")

    cache = HistoryCache(fetcher)
    for _ in range(2):
        with pytest.raises(RuntimeError):
            cache.get("NVDA", "1M")
    assert len(calls) == 2


def test_fetch_splits_one_yahoo_batch(monkeypatch: pytest.MonkeyPatch) -> None:
    seen: dict[str, str] = {}

    def fake_quotes(tickers: dict[str, str]) -> list[Quote]:
        seen.update(tickers)
        return [Quote(name, symbol, price=1.0) for name, symbol in tickers.items()]

    monkeypatch.setattr(service, "fetch_quotes", fake_quotes)
    monkeypatch.setattr(service, "fetch_country_stats", lambda: make_snapshot().countries)
    monkeypatch.setattr(service, "cache_checked_at", lambda: 123.0)

    snap = service.fetch()
    assert [q.symbol for q in snap.quotes] == list(TICKERS.values())
    assert [q.symbol for q in snap.extras] == list(EXTRAS.values())
    assert snap.fx["INR"].symbol == "INR=X"
    assert "USD" not in snap.fx  # the US row needs no FX quote
    assert snap.macro_fetched == 123.0
    assert len(seen) == len(snap.quotes) + len(snap.extras) + len(snap.fx)
