# market-cli

A live terminal dashboard with two panels:

- **Stocks:** Vanguard S&P 500 ETF (`VOO`), NVIDIA (`NVDA`) and SpaceX (`SPCX`), using free Yahoo Finance data through `yfinance`.
- **Country snapshot (US and India):** currency (with the live USD→INR rate), GDP growth, unemployment, inflation, policy interest rate and government debt to GDP.

## Data sources

No API keys are needed.

| Data | Source |
|---|---|
| Stock prices, USD/INR | Yahoo Finance (`yfinance`) |
| GDP growth, unemployment, inflation, debt/GDP | [IMF DataMapper](https://www.imf.org/external/datamapper) (World Economic Outlook). Shows the current year's value, which is an IMF estimate. |
| Policy interest rate | [BIS central bank policy rates](https://data.bis.org/topics/CBPOL) (Fed target midpoint, RBI repo rate) |

Country data is cached for 12 hours, in `%LOCALAPPDATA%\market-cli\Cache\macro.json` on Windows and `~/Library/Caches/market-cli/macro.json` on macOS. If a source can't be reached, the last cached value is shown and marked `cached`. The first run takes about 15 seconds while it fetches the IMF data.

## Install uv

- **Windows:** `winget install astral-sh.uv`
- **macOS:** `brew install uv`

## Run

```sh
uv sync                     # creates .venv and installs locked deps
uv run market               # live dashboard, refreshes every 60s (Ctrl+C to quit)
uv run market --interval 30 # custom refresh (minimum 15s)
uv run market --once        # print one snapshot and exit
```

These commands are the same on Windows and macOS.

To run `market` from anywhere without `uv run`:

```sh
uv tool install .
market
```

## Changing tickers

Edit `TICKERS` (stocks) or `COUNTRIES` (country panel) in `src/market_cli/config.py`.
