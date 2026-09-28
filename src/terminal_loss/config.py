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

# Display name -> IMF / BIS country codes, currency, Yahoo FX symbol (local currency per USD) and symbol.
# Germany uses the ECB policy rate (BIS area XM).
COUNTRIES: dict[str, dict[str, str | None]] = {
    "United States": {"imf": "USA", "bis": "US", "currency": "USD", "fx": None, "sym": "$"},
    "India": {"imf": "IND", "bis": "IN", "currency": "INR", "fx": "INR=X", "sym": "₹"},
    "China": {"imf": "CHN", "bis": "CN", "currency": "CNY", "fx": "CNY=X", "sym": "¥"},
    "Japan": {"imf": "JPN", "bis": "JP", "currency": "JPY", "fx": "JPY=X", "sym": "¥"},
    "Germany": {"imf": "DEU", "bis": "XM", "currency": "EUR", "fx": "EUR=X", "sym": "€"},
    "United Kingdom": {"imf": "GBR", "bis": "GB", "currency": "GBP", "fx": "GBP=X", "sym": "£"},
    "Canada": {"imf": "CAN", "bis": "CA", "currency": "CAD", "fx": "CAD=X", "sym": "C$"},
    "Brazil": {"imf": "BRA", "bis": "BR", "currency": "BRL", "fx": "BRL=X", "sym": "R$"},
}

# BIS area -> central bank, for the policy-rate note in the trend panel
CENTRAL_BANKS: dict[str, str] = {
    "US": "Fed",
    "IN": "RBI",
    "CN": "PBoC",
    "JP": "BoJ",
    "XM": "ECB",
    "GB": "BoE",
    "CA": "BoC",
    "BR": "BCB",
}

MACRO_TTL_HOURS = 12
