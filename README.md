<div align="center">

# ▶ Terminal Loss

**A live market dashboard for your terminal and your browser.**

Stocks, crypto, rates, commodities and country macro data, refreshed every minute, no API keys.

[![CI](https://github.com/Etezazi-Industries/terminal-loss/actions/workflows/ci.yml/badge.svg)](https://github.com/Etezazi-Industries/terminal-loss/actions/workflows/ci.yml)
![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/web-React%2019-61DAFB?logo=react&logoColor=black)
![uv](https://img.shields.io/badge/managed%20with-uv-DE5FE9)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](LICENSE)

[Features](#-features) · [Quick start](#-quick-start) · [Terminal](#-terminal-dashboard) · [Web](#-web-dashboard) · [API](#-http-api) · [Development](#-development) · [Deployment](#-deployment)

</div>

<!-- Screenshots go here: web dashboard (Markets + Countries) and the terminal dashboard. -->

---

## ✨ Features

|  | Markets | Countries |
|---|---|---|
| **What** | Index & ETF, big-tech stocks and Bitcoin, plus VIX, US 10Y, gold, WTI crude and the dollar index | GDP growth, unemployment, inflation, policy rate and debt/GDP for 8 major economies, with live FX |
| **Terminal** | Breadth line, day and 52-week range bars, volume vs 3-month average, 5-day sparklines | Sortable table with in-cell bars and a 10-year trend panel for the selected country |
| **Web** | 1D heatmap, grouped stocks table and a detail chart over 1D / 5D / 1M / 1Y | Sortable table beside 10-year trend charts |

- 🖥️ **Two front ends, one API.** The Rich terminal UI and the React web app both read from the same FastAPI server.
- ⌨️ **Keyboard first.** The same keys work in the terminal and in the browser.
- 🔑 **No API keys.** Data comes from Yahoo Finance, the IMF and the BIS.
- 🕒 **Exchange-aware.** NYSE and BSE session status, and charts in each exchange's own time zone.
- 🛡️ **Built to be shared.** Caching keeps upstream calls down however many people are watching; the last good data is kept if a source fails.

## 🚀 Quick start

Terminal Loss uses [uv](https://docs.astral.sh/uv/) (`winget install astral-sh.uv` on Windows, `brew install uv` on macOS).

```sh
git clone https://github.com/Etezazi-Industries/terminal-loss.git
cd terminal-loss
uv sync

uv run market        # terminal dashboard
uv run market-api    # API + web dashboard on http://127.0.0.1:8000 (build the web app first, see below)
```

## 🖥️ Terminal dashboard

```sh
uv run market                          # live dashboard, refreshes every 60s
uv run market --interval 30            # custom refresh (minimum 15s)
uv run market --tab countries          # start on the Countries tab
uv run market --once                   # print one snapshot of both tabs and exit
uv run market --once --tab markets     # print one tab
uv run market --api http://host:8000   # use a remote market-api server
```

`market` talks to `--api` (default `$MARKET_API_URL` or `http://127.0.0.1:8000`). If nothing answers there, it starts an API server in-process, so it works on its own too. To run it from anywhere without `uv run`: `uv tool install .`

<details>
<summary><b>Preview: Markets tab</b></summary>

```
 1 Markets  2 Countries  │ ● NYSE open  13:29 ET │ ● BSE closed  22:59 IST                                      next refresh in 23s

Breadth  1 ▲  9 ▼ │ Best  NVDA +2.27%   Worst  META −3.53%                                             sorted by group · s to cycle

╭─ Stocks ────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                 │
│ SYMBOL      NAME            PRICE       CHANGE        %          DAY RANGE               52-WEEK RANGE         VOL       5 DAYS │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ INDEX &                                                                                                                         │
│ ETF                                                                                                                             │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ VOO         Vanguard…      705.01       ▼ 6.34   −0.89%   701.98 ─────●─── 707.31   578.46 ───────●─ 716.39   0.7×   ██▄▃▂▃▃▆▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ BSESN       Sensex      72,771.72   ▼ 1,124.02   −1.52%    72.7k ●──────── 73.7k     71.5k ─●─────── 86.2k     N/A   █▇██▅▄▄▄▁▁ │
│                                                                                                                                 │
│ STOCKS                                                                                                                          │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ NVDA        NVIDIA         230.11       ▲ 5.11   +2.27%   228.46 ───●───── 233.21   164.27 ───────●─ 236.54   0.8×   ▆▇▃▃▁▂▂▃█▇ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ SPCX        SpaceX         146.54       ▼ 2.24   −1.51%   145.66 ─●─────── 150.80   104.83 ───●───── 225.64   0.6×   ██▇▅▂▂▁▃▂▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ GOOGL       Google         341.80       ▼ 2.20   −0.64%   339.56 ────●──── 343.59   235.84 ─────●─── 408.61   0.3×   █▅▂▁▁▂▂▃▂▂ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ AMZN        Amazon         246.91       ▼ 3.07   −1.23%   244.73 ──────●── 247.77   196.00 ────●──── 287.20   0.4×   █▆▃▂▁▃▂▄▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ META        Meta           721.43      ▼ 26.42   −3.53%   717.25 ─●─────── 750.58   520.26 ──────●── 779.82   0.9×   ▅▄▄▅▇█▅▅▁▁ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ MSFT        Microsoft      511.85       ▼ 6.04   −1.17%   502.22 ───────●─ 513.33   349.20 ──────●── 553.72   0.3×   ▂▂▂▃▁▂▇█▅▇ │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ AAPL        Apple          339.98       ▼ 1.48   −0.43%   339.32 ─●─────── 342.99   243.42 ────────● 345.34   0.3×   ▆█▂▂▂▃▁▆▇▆ │
│                                                                                                                                 │
│ CRYPTO                                                                                                                          │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ BTC         Bitcoin     83,865.76     ▼ 596.38   −0.71%    82.6k ─────●─── 84.8k    57.7k ───●───── 126.2k    1.5×   ▆▆█▄▄▅▇▇▁▃ │
│ VOL = today's volume vs 3-month average, amber at 1.5× or more                                                                  │
│                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ Rates & commodities ───────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                 │
│ VIX Volatility                             US 10Y Treasury yield                     GOLD per oz                                │
│ 15.79 ▲ 6.19% ▃▁▁▇▆▄█▆                     5.228% ▲ 0.85% ▁▁▄▅▆█▇█                   4,168.10 ▼ 1.48% █▆▆▆▅▆▂▁                  │
│                                                                                                                                 │
│ WTI Crude oil                              DXY Dollar index                                                                     │
│ 92.18 ▼ 1.93% ▁▄▄█▆▅█▅                     101.12 ▲ 0.00% ▁▅▆██▄▆▆                                                              │
│                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

Yahoo Finance · 5-day hourly closes                                                      1 2 tabs   s sort   r refresh now   q quit
```

</details>

<details>
<summary><b>Preview: Countries tab</b></summary>

```
 1 Markets  2 Countries  │ IMF WEO estimates for 2026 · policy rates BIS · FX live              fetched 12:59   next refresh in 23s

╭─ Countries ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                 │
│   COUNTRY          CCY · PER $   GDP GROWTH ▼        UNEMPLOYMENT       INFLATION          POLICY RATE        DEBT / GDP        │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│ ▌ India            INR ₹95.97      6.5%   ███████      4.9%   █████       4.7%   ███████    5.25%   ██▋        83.4%   ██▉      │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   China            CNY ¥6.70       4.4%   ████▊        5.1%   █████▎      1.2%   █▊            3%   █▌        106.9%   ███▋     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   United States    USD $1.00       2.3%   ██▌          4.4%   ████▌       3.2%   ████▊     3.875%   ██        125.8%   ████▎    │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Brazil           BRL R$5.21      1.9%   ██           6.8%   ███████       4%   ██████    13.75%   ███████    96.5%   ███▎     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Canada           CAD C$1.42      1.5%   █▋           6.5%   ██████▊     2.5%   ███▊       2.25%   █▏        110.7%   ███▊     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Germany          EUR €0.88       0.8%   ▉            3.9%   ████        2.7%   ████        2.5%   █▎         64.6%   ██▎      │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   United Kingdom   GBP £0.75       0.8%   ▉            5.6%   █████▊      3.2%   ████▊      3.75%   █▉        103.6%   ███▌     │
│ ─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────── │
│   Japan            JPY ¥157.09     0.7%   ▊            2.5%   ██▋         2.2%   ███▎          1%   ▌         204.4%   ███████  │
│ Bars scale to the highest value in each column · * cached · N/A = no IMF series                                                 │
│                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭─ India · 10-year trend ─────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                 │
│ GDP growth                Unemployment              Inflation                Policy rate              Gov. debt / GDP           │
│ 6.5%  ▇▇▇▅▁█▇▇▇▇▇         4.9%  █▆██▅▂▁▁▁▁▁         4.7%  ▅▃▃▅▇▆█▆▅▁▅        5.25%                    83.4%  ▁▁▂▃█▆▆▆▆▆▆        │
│ IMF WEO                   IMF WEO                   IMF WEO                  RBI · 2026-07-23         IMF WEO                   │
│                                                                                                                                 │
│ 2016 → 2026 · same IMF DataMapper call                                                                                          │
│                                                                                                                                 │
╰─────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

IMF WEO (year shown) · policy rates: BIS                      1 2 tabs   ↑↓ select country   s sort column   r refresh now   q quit
```

</details>

**What you see**

- **Status line:** the active tab, NYSE / BSE session status with local times (Markets) or the data sources and macro cache age (Countries), and a countdown to the next refresh.
- **Markets:** a breadth line (advancers / decliners, best and worst mover), then Stocks grouped into Index & ETF (`VOO`, `^BSESN`), Stocks (`NVDA`, `SPCX`, `GOOGL`, `AMZN`, `META`, `MSFT`, `AAPL`) and Crypto (`BTC-USD`). Each row shows price, change, where the price sits in its day and 52-week ranges, volume vs its 3-month average (amber at 1.5× or more) and a 5-day sparkline. Narrow terminals drop the 5 DAYS column below 120 columns and VOL below 105. **Rates & commodities** follows.
- **Countries:** the United States, India, China, Japan, Germany (ECB policy rate), the United Kingdom, Canada and Brazil. Bars scale to the highest value in each column (hidden below 130 columns), the sorted column is amber and `*` marks a cached value. The **10-year trend** panel shows sparklines for the selected country.

## ⌨️ Keys

Same in the terminal and the browser.

| Key | Action |
|---|---|
| `1` / `2` / `Tab` | Markets / Countries / other tab |
| `s` | Cycle the sort: group → % change → name (Markets), or the sort column (Countries) |
| `↑` `↓` / `k` `j` | Move the selected stock (web) or country |
| `←` `→` | Change the chart range: 1D / 5D / 1M / 1Y (web) |
| `r` | Refresh now |
| `q` | Quit (terminal; Ctrl+C works too) |

## 🌐 Web dashboard

A React + Vite app in `web/`, served by `market-api` at `/`. Needs Node.js 20.19+.

```sh
cd web
npm install
npm run dev     # http://localhost:5173, proxies /api to market-api on :8000 (start it first)
npm run build   # writes web/dist, which market-api serves at /
```

Tabs, heatmap tiles, rows, sort controls, range buttons and column headers are all clickable. URL options:

| Parameter | Effect |
|---|---|
| `?interval=30` | Refresh interval in seconds (minimum 15) |
| `?tab=countries` | Starting tab |

## 🔌 HTTP API

```
Yahoo / IMF / BIS ─▶ market-api (FastAPI) ─┬─▶ market  (terminal, Rich)
                                            └─▶ web/    (React + Vite)
```

| Endpoint | Returns |
|---|---|
| `GET /api/snapshot` | Quotes, rates & commodities, countries, FX and the macro cache time. Reused for 15 seconds, so all clients share one Yahoo fetch. `?force=true` asks for fresh data, but a snapshot younger than 15 seconds is still reused. If a refetch fails, the previous snapshot is served. |
| `GET /api/history?symbol=NVDA&range=1D` | `[{t, close}]` for the web chart: 5-minute bars for `1D`, hourly for `5D`, daily for `1M` and `1Y`. Only configured symbols are accepted. Cached from a minute (intraday) to an hour (`1Y`). |
| `GET /api/health` | `{"ok": true}` liveness check |
| `GET /docs` | Interactive OpenAPI docs |

```sh
uv run market-api                               # http://127.0.0.1:8000
uv run market-api --host 0.0.0.0 --port 9000    # or set $HOST / $PORT
```

Set `MARKET_WEB_DIST` to serve a web build from another directory.

## 📊 Data sources

| Data | Source |
|---|---|
| Stocks, index, crypto, rates & commodities; FX rates | Yahoo Finance via [`yfinance`](https://github.com/ranaroussi/yfinance), in one batch |
| GDP growth, unemployment, inflation, debt/GDP | [IMF DataMapper](https://www.imf.org/external/datamapper) (World Economic Outlook). The current year's value is an IMF estimate; the 10-year trend comes from the same request. |
| Policy interest rate | [BIS central bank policy rates](https://data.bis.org/topics/CBPOL) (e.g. Fed target midpoint, RBI repo rate, ECB deposit rate for Germany) |

Country data is cached on disk for 12 hours (`%LOCALAPPDATA%\terminal-loss\Cache\macro.json` on Windows, `~/Library/Caches/terminal-loss/macro.json` on macOS, `~/.cache/terminal-loss/macro.json` on Linux). If a source can't be reached, the last cached value is shown, marked `*` in the table and `cached` in the trend panel. The first run takes about 15 seconds while it fetches the IMF data; later refreshes take about 5.

## 🛠️ Configuration

Edit `src/terminal_loss/config.py`:

| Setting | Controls |
|---|---|
| `GROUPS` | Markets rows and their groups |
| `EXTRAS` / `EXTRA_LABELS` | Rates & commodities |
| `COUNTRIES` | Countries tab: IMF / BIS codes, currency and FX symbol |
| `REFRESH_SECONDS` / `MIN_REFRESH_SECONDS` | Default and minimum refresh interval |

## 🧪 Development

```sh
uv run pytest            # Python tests
uv run ruff check .      # Python lint
uv run ruff format .     # Python format

cd web
npm test                 # web unit tests (Vitest)
npm run lint             # Biome lint + format check (npm run format fixes)
npm run typecheck        # TypeScript
```

[CI](.github/workflows/ci.yml) runs all of these on every push and pull request, builds the web app and smoke-tests `market-api` serving it.

```
src/terminal_loss/
├── cli.py         terminal dashboard (market)
├── ui.py          Rich renderables for both tabs
├── keys.py        non-blocking key reader (Windows + POSIX)
├── data.py        Yahoo Finance quotes and chart history
├── macro.py       IMF + BIS country data, cached on disk
├── config.py      tickers, countries, refresh intervals
└── api/
    ├── app.py     FastAPI app (market-api)
    ├── service.py snapshot fetch + in-memory caches
    ├── schema.py  JSON shape shared by server and client
    └── client.py  Python client, with in-process fallback server
web/src/           React dashboard
tests/             pytest suite
```

## ☁️ Deployment

Terminal Loss runs on [Render](https://render.com)'s free tier. [`render.yaml`](render.yaml) describes the service as a Blueprint. For a service set up by hand:

| Setting | Value |
|---|---|
| Build command | `pip install uv && uv sync --locked --no-dev && cd web && npm ci && npm run build` |
| Start command | `uv run --no-dev market-api --host 0.0.0.0` (port from `$PORT`) |
| Health check path | `/api/health` |

Run one instance with one process, since the snapshot and chart caches live in memory. The server fetches a snapshot at startup, so the first visitor after a free-tier spin-up waits less. It sends security headers (CSP, `nosniff`, no framing), long-lived caching for the hashed files under `/assets/`, and gzip.

## 📄 License

[MIT](LICENSE)

<div align="center"><sub>Market data is for information only and may be delayed. Not investment advice.</sub></div>
