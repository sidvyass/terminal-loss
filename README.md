# market-cli

A live terminal dashboard with a status line, two panels and a footer:

```
● Market open │ Mon 28 Sep · 10:42:15 ET                                                        next refresh in 23s

╭─ Stocks ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│  SYMBOL    NAME                PRICE   CHANGE        %          DAY RANGE               52-WEEK RANGE            5 DAYS  │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  VOO       Vanguard S&P 500   612.84   ▲ 4.73   +0.78%   607.55 ──────●── 614.20   489.30 ───────●─ 621.75   ▁▂▂▄▅▄▆▇▇█  │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  NVDA      NVIDIA             180.10   ▼ 3.45   −1.88%   179.20 ─●─────── 185.00   86.62 ──────●── 212.19    █▇▇▅▅▄▃▂▂▁  │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  SPCX      SpaceX             147.37   ▼ 1.41   −0.95%   145.66 ───●───── 150.80   104.83 ───●───── 225.64   ▇█▅▄▂▁▂▄▂▂  │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Country snapshot ───────────────────────────────────────────────────────────────────────────────────────────────────────╮
│  METRIC                   UNITED STATES                                 INDIA                                            │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  Currency                 USD                                           INR  ₹88.12 per $                                │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  GDP growth                   2%  ███▏        2026                        6.4%  ██████████  2026                         │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  Unemployment               4.2%  ██████████  2026                         N/A              no IMF series                │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  Inflation                  2.9%  █████████▍  2026                        3.1%  ██████████  2026                         │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  Policy rate              4.125%  ███████▌    2026-09-17                  5.5%  ██████████  2026-09-17                   │
│ ──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│  Gov. debt / GDP          122.5%  ██████████  2026                       81.3%  ██████▋     2026 · cached                │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

IMF WEO (year shown) · policy rates: BIS                                                              r refresh now   q quit
```

- **Status line:** the active tab, NYSE / BSE / crypto session status with local times, and a countdown to the next refresh.
- **Markets tab:** a breadth line (advancers / decliners, best and worst mover), then Stocks grouped into Index & ETF (Vanguard S&P 500 `VOO`, BSE Sensex `^BSESN`), Stocks (`NVDA`, `SPCX`, `GOOGL`, `AMZN`, `META`, `MSFT`, `AAPL`) and Crypto (`BTC-USD`). Each row shows price, change, where today's price sits in the day and 52-week ranges, today's volume vs its 3-month average (VOL, amber at 1.5× or more) and a 5-day sparkline. On narrow terminals the 5 DAYS column hides under 120 columns and VOL under 105. Below it, **Rates & commodities** shows VIX, the US 10-year yield, gold, WTI crude and the dollar index. All quotes come from one Yahoo Finance batch via `yfinance`.
- **Country snapshot (US and India):** currency (with the live USD→INR rate), GDP growth, unemployment, inflation, policy interest rate and government debt to GDP, each with a bar scaled against the other country.

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
uv run market               # live dashboard, refreshes every 60s
uv run market --interval 30 # custom refresh (minimum 15s)
uv run market --once        # print one snapshot of both tabs and exit (no countdown or key hints)
uv run market --once --tab countries  # print one tab (markets or countries)
uv run market --tab countries         # start the live dashboard on a given tab
```

These commands are the same on Windows and macOS.

### Keys (live dashboard)

| Key | Action |
|---|---|
| `1` / `2` / `Tab` | Switch to Markets / Countries / the other tab (no refetch; the countdown keeps running) |
| `s` | Markets: cycle the sort (group → % change → name) |
| `r` | Refresh now (resets the countdown) |
| `q` | Quit (Ctrl+C also works) |

To run `market` from anywhere without `uv run`:

```sh
uv tool install .
market
```

## Changing tickers

Edit `TICKERS` (stocks) or `COUNTRIES` (country panel) in `src/market_cli/config.py`.
