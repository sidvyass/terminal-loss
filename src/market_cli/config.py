# Display name -> Yahoo Finance symbol
TICKERS: dict[str, str] = {
    "Vanguard S&P 500": "VOO",
    "NVIDIA": "NVDA",
    "SpaceX": "SPCX",
    "Google": "GOOGL",
    "Amazon": "AMZN",
    "Meta": "META",
    "Microsoft": "MSFT",
    "Apple": "AAPL",
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
