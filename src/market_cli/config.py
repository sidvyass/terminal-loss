# Group label -> {display name -> Yahoo Finance symbol}; the Markets tab shows rows in this order.
GROUPS: dict[str, dict[str, str]] = {
    "INDEX & ETF": {"Vanguard S&P 500": "VOO", "Sensex": "^BSESN"},
    "STOCKS": {
        "NVIDIA": "NVDA",
        "SpaceX": "SPCX",
        "Google": "GOOGL",
        "Amazon": "AMZN",
        "Meta": "META",
        "Microsoft": "MSFT",
        "Apple": "AAPL",
    },
    "CRYPTO": {"Bitcoin": "BTC-USD"},
}
TICKERS: dict[str, str] = {n: s for g in GROUPS.values() for n, s in g.items()}  # flat, for fetching

# Rates & commodities panel: key -> Yahoo symbol, and the label shown next to the key
EXTRAS: dict[str, str] = {"VIX": "^VIX", "US 10Y": "^TNX", "GOLD": "GC=F", "WTI": "CL=F", "DXY": "DX-Y.NYB"}
EXTRA_LABELS: dict[str, str] = {
    "VIX": "Volatility",
    "US 10Y": "Treasury yield",
    "GOLD": "per oz",
    "WTI": "Crude oil",
    "DXY": "Dollar index",
}

REFRESH_SECONDS = 60
MIN_REFRESH_SECONDS = 15  # stay well clear of Yahoo rate limits

# Display name -> IMF / BIS country codes and currency
COUNTRIES: dict[str, dict[str, str]] = {
    "United States": {"imf": "USA", "bis": "US", "currency": "USD"},
    "India": {"imf": "IND", "bis": "IN", "currency": "INR"},
}

FX_SYMBOL = "INR=X"  # USD -> INR
MACRO_TTL_HOURS = 12
