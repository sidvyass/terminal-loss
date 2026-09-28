# market-cli

A live terminal dashboard with two tabs. Switch with `1` / `2` or `Tab`.

**Markets** (`1`):

```
 1 Markets  2 Countries  │ ● NYSE open  13:00 ET │ ● BSE closed  22:30 IST │ ● Crypto 24/7                      next refresh in 23s

Breadth  1 ▲  9 ▼ │ Best  NVDA +2.66%   Worst  META −3.35%                                             sorted by group · s to cycle

╭─ Stocks ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ SYMBOL      NAME            PRICE       CHANGE        %          DAY RANGE               52-WEEK RANGE         VOL       5 DAYS │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ INDEX &                                                                                                                         │
│ ETF                                                                                                                             │
│ VOO         Vanguard…      705.13       ▼ 6.22   −0.87%   701.98 ─────●─── 707.31   578.46 ───────●─ 716.39   0.7×   ██▄▃▂▃▃▆▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ BSESN       Sensex      72,771.72   ▼ 1,124.02   −1.52%    72.7k ●──────── 73.7k     71.5k ─●─────── 86.2k     N/A   █▇██▅▄▄▄▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ STOCKS                                                                                                                          │
│ NVDA        NVIDIA         230.99       ▲ 5.99   +2.66%   228.46 ────●──── 233.21   164.27 ───────●─ 236.54   0.7×   ▆▇▃▃▁▂▂▃██ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ SPCX        SpaceX         147.01       ▼ 1.77   −1.19%   145.66 ──●────── 150.80   104.83 ───●───── 225.64   0.6×   ██▇▅▂▂▁▃▂▂ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ GOOGL       Google         340.96       ▼ 3.04   −0.88%   339.56 ───●───── 343.59   235.84 ─────●─── 408.61   0.3×   █▅▂▁▁▂▂▃▂▂ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ AMZN        Amazon         246.78       ▼ 3.20   −1.28%   244.73 ──────●── 247.71   196.00 ────●──── 287.20   0.3×   █▆▃▂▁▃▂▄▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ META        Meta           722.79      ▼ 25.06   −3.35%   717.25 ─●─────── 750.58   520.26 ──────●── 779.82   0.8×   ▅▄▄▄▇█▅▅▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ MSFT        Microsoft      512.21       ▼ 5.68   −1.10%   502.22 ───────●─ 513.18   349.20 ──────●── 553.72   0.3×   ▂▂▂▃▁▂▇█▅▇ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ AAPL        Apple          340.87       ▼ 0.59   −0.17%   339.32 ───●───── 342.99   243.42 ────────● 345.34   0.3×   ▆█▂▂▂▃▁▆▇▇ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ CRYPTO                                                                                                                          │
│ BTC         Bitcoin     83,677.39     ▼ 784.74   −0.93%    82.6k ────●──── 84.8k    57.7k ───●───── 126.2k    1.5×   ▆▂█▄▄▄▇▇▁▂ │
│ VOL = today's volume vs 3-month average, amber at 1.5× or more                                                                  │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Rates & commodities ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ VIX Volatility                             US 10Y Treasury yield                     GOLD per oz                                │
│ 15.99 ▲ 7.53% ▃▁▁▇▅▄█▇                     5.247% ▲ 1.22% ▁▁▄▅▆▇▇█                   4,161.80 ▼ 1.62% █▆▆▅▅▆▃▁                  │
│                                                                                                                                 │
│ WTI Crude oil                              DXY Dollar index                                                                     │
│ 93.29 ▼ 0.74% ▁▄▄█▆▅█▇                     101.15 ▲ 0.03% ▁▅▆██▄▆▆                                                              │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Yahoo Finance · 5-day hourly closes                                                      1 2 tabs   s sort   r refresh now   q quit
```

**Countries** (`2`):

```
 1 Markets  2 Countries  │ IMF WEO estimates for 2026 · policy rates BIS · FX live              fetched 12:59   next refresh in 23s

╭─ Countries ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│   COUNTRY          CCY · PER $   GDP GROWTH ▼        UNEMPLOYMENT       INFLATION          POLICY RATE        DEBT / GDP        │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ ▌ India            INR ₹95.97      6.5%   ███████      4.9%   █████       4.7%   ███████    5.25%   ██▋        83.4%   ██▉      │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   China            CNY ¥6.70       4.4%   ████▊        5.1%   █████▎      1.2%   █▊            3%   █▌        106.9%   ███▋     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   United States    USD $1.00       2.3%   ██▌          4.4%   ████▌       3.2%   ████▊     3.875%   ██        125.8%   ████▎    │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Brazil           BRL R$5.22      1.9%   ██           6.8%   ███████       4%   ██████    13.75%   ███████    96.5%   ███▎     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Canada           CAD C$1.42      1.5%   █▋           6.5%   ██████▊     2.5%   ███▊       2.25%   █▏        110.7%   ███▊     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Germany          EUR €0.88       0.8%   ▉            3.9%   ████        2.7%   ████        2.5%   █▎         64.6%   ██▎      │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   United Kingdom   GBP £0.75       0.8%   ▉            5.6%   █████▊      3.2%   ████▊      3.75%   █▉        103.6%   ███▌     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Japan            JPY ¥157.31     0.7%   ▊            2.5%   ██▋         2.2%   ███▎          1%   ▌         204.4%   ███████  │
│ Bars scale to the highest value in each column · * cached · N/A = no IMF series                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ India · 10-year trend ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ GDP growth                Unemployment              Inflation                Policy rate              Gov. debt / GDP           │
│ 6.5%  ▇▇▇▅▁█▇▇▇▇▇         4.9%  █▆██▅▂▁▁▁▁▁         4.7%  ▅▃▃▅▇▆█▆▅▁▅        5.25%                    83.4%  ▁▁▂▃█▆▆▆▆▆▆        │
│ IMF WEO                   IMF WEO                   IMF WEO                  RBI · 2026-07-23         IMF WEO                   │
│                                                                                                                                 │
│ 2016 → 2026 · same IMF DataMapper call                                                                                          │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

IMF WEO (year shown) · policy rates: BIS                      1 2 tabs   ↑↓ select country   s sort column   r refresh now   q quit
```

- **Status line:** the active tab, then NYSE / BSE / crypto session status with local times (Markets) or the data sources and macro cache age (Countries), and a countdown to the next refresh.
- **Markets tab:** a breadth line (advancers / decliners, best and worst mover), then Stocks grouped into Index & ETF (Vanguard S&P 500 `VOO`, BSE Sensex `^BSESN`), Stocks (`NVDA`, `SPCX`, `GOOGL`, `AMZN`, `META`, `MSFT`, `AAPL`) and Crypto (`BTC-USD`). Each row shows price, change, where today's price sits in the day and 52-week ranges, today's volume vs its 3-month average (VOL, amber at 1.5× or more) and a 5-day sparkline. On narrow terminals the 5 DAYS column hides under 120 columns and VOL under 105. Below it, **Rates & commodities** shows VIX, the US 10-year yield, gold, WTI crude and the dollar index.
- **Countries tab:** the United States, India, China, Japan, Germany (ECB policy rate), the United Kingdom, Canada and Brazil, with each currency's live rate per US dollar, GDP growth, unemployment, inflation, policy rate and government debt to GDP. Bars scale to the highest value in each column (hidden under 130 columns). The sorted column is amber; `*` marks a cached value. Below it, a **10-year trend** panel shows sparklines for the selected country.

## Data sources

No API keys are needed.

| Data | Source |
|---|---|
| Stock, index, crypto, rates & commodities prices; FX rates | Yahoo Finance (`yfinance`), all in one batch |
| GDP growth, unemployment, inflation, debt/GDP | [IMF DataMapper](https://www.imf.org/external/datamapper) (World Economic Outlook). Shows the current year's value, which is an IMF estimate; the 10-year trend comes from the same request. |
| Policy interest rate | [BIS central bank policy rates](https://data.bis.org/topics/CBPOL) (e.g. Fed target midpoint, RBI repo rate, ECB deposit rate for Germany) |

Country data is cached for 12 hours, in `%LOCALAPPDATA%\market-cli\Cache\macro.json` on Windows and `~/Library/Caches/market-cli/macro.json` on macOS. If a source can't be reached, the last cached value is shown, marked `*` in the Countries table and `cached` in the trend panel. The first run takes about 15 seconds while it fetches the IMF data; later refreshes take about 5 seconds.

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
| `s` | Markets: cycle the sort (group → % change → name). Countries: cycle the sort column (GDP → unemployment → inflation → policy rate → debt/GDP → name) |
| `↑` / `↓` (or `k` / `j`) | Countries: move the selected country (drives the 10-year trend panel) |
| `r` | Refresh now (resets the countdown) |
| `q` | Quit (Ctrl+C also works) |

To run `market` from anywhere without `uv run`:

```sh
uv tool install .
market
```

## Changing tickers

Edit `GROUPS` (Markets rows), `EXTRAS` (Rates & commodities) or `COUNTRIES` (Countries tab) in `src/market_cli/config.py`.
