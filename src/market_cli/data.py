from dataclasses import dataclass, field

import yfinance as yf


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


def fetch_quotes(tickers: dict[str, str]) -> list[Quote]:
    batch = yf.Tickers(" ".join(tickers.values()))
    quotes = []
    for name, symbol in tickers.items():
        quote = Quote(name=name, symbol=symbol)
        try:
            info = batch.tickers[symbol].fast_info
            quote.price = _get(info, "lastPrice")
            quote.prev_close = _get(info, "previousClose")
            quote.day_low = _get(info, "dayLow")
            quote.day_high = _get(info, "dayHigh")
            quote.year_low = _get(info, "yearLow")
            quote.year_high = _get(info, "yearHigh")
            quote.volume = _get(info, "lastVolume")
            quote.avg_volume = _get(info, "threeMonthAverageVolume")
            quote.history = batch.tickers[symbol].history(period="5d", interval="1h")["Close"].dropna().tolist()
            if quote.price is None:
                quote.error = "no data"
        except Exception as exc:  # one bad ticker shouldn't take down the dashboard
            quote.error = str(exc) or type(exc).__name__
        quotes.append(quote)
    return quotes
