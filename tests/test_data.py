import pandas as pd
import pytest

from terminal_loss import data
from terminal_loss.data import Quote


def test_quote_change() -> None:
    q = Quote("NVIDIA", "NVDA", price=110.0, prev_close=100.0)
    assert q.change == pytest.approx(10.0)
    assert q.pct_change == pytest.approx(10.0)
    assert Quote("X", "X", price=1.0).change is None
    assert Quote("X", "X", price=1.0, prev_close=0.0).pct_change is None


def _closes(values: list[float | None]) -> pd.DataFrame:
    index = pd.date_range("2026-09-28 09:30", periods=len(values), freq="h", tz="America/New_York")
    return pd.DataFrame({"Close": values}, index=index)


class FakeInfo(dict):
    timezone = "America/New_York"


class FakeTicker:
    def __init__(self, info: dict, closes: pd.DataFrame | None = None, error: Exception | None = None) -> None:
        self.fast_info = FakeInfo(info)
        self._closes = closes if closes is not None else _closes([])
        self._error = error

    def history(self, period: str, interval: str) -> pd.DataFrame:
        if self._error:
            raise self._error
        return self._closes


def test_fill_reads_fast_info_and_history() -> None:
    ticker = FakeTicker({"lastPrice": 230.1, "previousClose": 225, "dayLow": None}, _closes([1.0, None, 3.0]))
    q = data._fill(Quote("NVIDIA", "NVDA"), ticker)
    assert (q.price, q.prev_close, q.day_low, q.error) == (230.1, 225.0, None, None)
    assert q.history == [1.0, 3.0]  # NaN closes dropped
    assert q.history_times[0].startswith("2026-09-28T09:30:00")
    assert q.timezone == "America/New_York"


def test_fill_marks_missing_price_and_errors() -> None:
    assert data._fill(Quote("X", "X"), FakeTicker({})).error == "no data"
    failed = data._fill(Quote("X", "X"), FakeTicker({"lastPrice": 1.0}, error=RuntimeError("rate limited")))
    assert failed.error == "rate limited"


def test_fetch_history(monkeypatch: pytest.MonkeyPatch) -> None:
    requested = []

    class FakeYfTicker:
        def __init__(self, symbol: str) -> None:
            self.symbol = symbol

        def history(self, period: str, interval: str) -> pd.DataFrame:
            requested.append((self.symbol, period, interval))
            return _closes([10.0, 11.0])

    monkeypatch.setattr(data.yf, "Ticker", FakeYfTicker)
    points = data.fetch_history("NVDA", "1D")
    assert requested == [("NVDA", "1d", "5m")]
    assert [v for _, v in points] == [10.0, 11.0]


def test_fetch_quotes_keeps_input_order(monkeypatch: pytest.MonkeyPatch) -> None:
    class FakeTickers:
        def __init__(self, symbols: str) -> None:
            self.tickers = {s: FakeTicker({"lastPrice": float(i)}) for i, s in enumerate(symbols.split())}

    monkeypatch.setattr(data.yf, "Tickers", FakeTickers)
    quotes = data.fetch_quotes({"B": "BBB", "A": "AAA", "C": "CCC"})
    assert [(q.name, q.price) for q in quotes] == [("B", 0.0), ("A", 1.0), ("C", 2.0)]
