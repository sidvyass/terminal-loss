from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field

import yfinance as yf

FETCH_WORKERS = 8  # parallel per-symbol requests; modest to stay clear of Yahoo rate limits


@dataclass
class Quote:
    name: str
    symbol: str
    price: float | None = None
    prev_close: float | None = None
    day_low: float | None = None
    day_high: float | None = None
    year_low: float | None = None
    year_high: float | None = None
    volume: float | None = None
    avg_volume: float | None = None  # 3-month average daily volume
    error: str | None = None
    history: list[float] = field(default_factory=list)  # ~5 days of hourly closes
    history_times: list[str] = field(default_factory=list)  # ISO timestamps of `history`, exchange time
    timezone: str | None = None  # exchange time zone, e.g. "America/New_York"

    @property
    def change(self) -> float | None:
        if self.price is None or self.prev_close is None:
            return None
        return self.price - self.prev_close

    @property
    def pct_change(self) -> float | None:
        if self.change is None or not self.prev_close:
            return None
        return self.change / self.prev_close * 100


def _get(info, key: str) -> float | None:
    try:
        value = info[key]
    except Exception:
        return None
    return float(value) if value is not None else None


def _fill(quote: Quote, ticker: yf.Ticker) -> Quote:
    try:
        info = ticker.fast_info
        quote.price = _get(info, "lastPrice")
        quote.prev_close = _get(info, "previousClose")
        quote.day_low = _get(info, "dayLow")
        quote.day_high = _get(info, "dayHigh")
        quote.year_low = _get(info, "yearLow")
        quote.year_high = _get(info, "yearHigh")
        quote.volume = _get(info, "lastVolume")
        quote.avg_volume = _get(info, "threeMonthAverageVolume")
        try:
            quote.timezone = info.timezone
        except Exception:
            pass  # optional: the web chart falls back to the viewer's time zone
        closes = ticker.history(period="5d", interval="1h")["Close"].dropna()
        quote.history = closes.tolist()
        quote.history_times = [t.isoformat() for t in closes.index]
        if quote.price is None:
            quote.error = "no data"
    except Exception as exc:  # one bad ticker shouldn't take down the dashboard
        quote.error = str(exc) or type(exc).__name__
    return quote


# Chart range -> yfinance history(period, interval); 5D comes with the snapshot (Quote.history).
HISTORY_RANGES: dict[str, tuple[str, str]] = {
    "1D": ("1d", "5m"),
    "5D": ("5d", "1h"),
    "1M": ("1mo", "1d"),
    "1Y": ("1y", "1d"),
}


def fetch_history(symbol: str, range_: str) -> list[tuple[str, float]]:
    """(ISO timestamp in exchange time, close) pairs for one chart range."""
    period, interval = HISTORY_RANGES[range_]
    closes = yf.Ticker(symbol).history(period=period, interval=interval)["Close"].dropna()
    return [(t.isoformat(), float(v)) for t, v in closes.items()]


def fetch_quotes(tickers: dict[str, str]) -> list[Quote]:
    """One batch for all symbols; each symbol's requests run on a small thread pool. Keeps input order."""
    batch = yf.Tickers(" ".join(tickers.values()))
    with ThreadPoolExecutor(max_workers=FETCH_WORKERS) as pool:
        futures = [
            pool.submit(_fill, Quote(name=name, symbol=symbol), batch.tickers[symbol])
            for name, symbol in tickers.items()
        ]
    return [f.result() for f in futures]
