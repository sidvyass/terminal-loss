import argparse
import math
import time
from dataclasses import dataclass
from typing import Literal

from rich.console import Console, RenderableType
from rich.live import Live

from market_cli.config import FX_SYMBOL, MIN_REFRESH_SECONDS, REFRESH_SECONDS, TICKERS
from market_cli.data import Quote, fetch_quotes
from market_cli.keys import KeyReader
from market_cli.macro import CountryStats, cache_checked_at, fetch_country_stats
from market_cli.ui import THEME, build_countries, build_dashboard, build_footer, build_header, build_markets

LOADING = "Fetching quotes and country data… (the first run takes about 15s)"
KEY_POLL_SECONDS = 0.05

Tab = Literal["markets", "countries"]


@dataclass
class Snapshot:
    quotes: list[Quote]
    countries: list[CountryStats]
    usd_inr: Quote | None
    macro_fetched: float | None


@dataclass
class View:
    tab: Tab = "markets"


def fetch() -> Snapshot:
    # Fetch the FX rate in the same batch as the stock quotes.
    quotes = fetch_quotes({**TICKERS, "USD/INR": FX_SYMBOL})
    usd_inr = quotes.pop()
    countries = fetch_country_stats()
    return Snapshot(quotes, countries, usd_inr, cache_checked_at())


def build_tab(data: Snapshot, tab: str, width: int) -> list[RenderableType]:
    if tab == "markets":
        return build_markets(data.quotes, width)
    if tab == "countries":
        return build_countries(data.countries, data.usd_inr, width)
    return build_tab(data, "markets", width) + build_tab(data, "countries", width)


def handle_key(key: str, view: View) -> bool:
    """Apply a view key (tabs); returns True if the view changed. Never refetches."""
    if key == "1":
        view.tab = "markets"
    elif key == "2":
        view.tab = "countries"
    elif key == "\t":
        view.tab = "countries" if view.tab == "markets" else "markets"
    else:
        return False
    return True


def main() -> None:
    parser = argparse.ArgumentParser(prog="market", description="Live market dashboard")
    parser.add_argument(
        "--interval",
        type=int,
        default=REFRESH_SECONDS,
        help=f"refresh interval in seconds (default {REFRESH_SECONDS}, min {MIN_REFRESH_SECONDS})",
    )
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    parser.add_argument(
        "--tab",
        choices=["markets", "countries", "all"],
        default=None,
        help="tab to show: with --once, which tab(s) to print (default all); live, the starting tab (default markets)",
    )
    args = parser.parse_args()

    console = Console(theme=THEME)
    try:
        with console.status(LOADING):
            data = fetch()
    except KeyboardInterrupt:
        return

    if args.once:
        tab = args.tab or "all"
        body = build_tab(data, tab, console.width)
        console.print(build_dashboard(build_header(tab, None, macro_fetched=data.macro_fetched), body, build_footer(tab, live=False)))
        return

    view = View(tab="countries" if args.tab == "countries" else "markets")
    interval = max(args.interval, MIN_REFRESH_SECONDS)
    try:
        with KeyReader() as keys, Live(console=console, screen=True, auto_refresh=False) as live:
            body, body_key = None, None
            next_at = time.monotonic() + interval
            force = False
            while True:
                remaining = math.ceil(next_at - time.monotonic())
                if remaining <= 0 or force:
                    header = build_header(view.tab, None, refreshing=True, macro_fetched=data.macro_fetched)
                    live.update(build_dashboard(header, body or [], build_footer(view.tab, live=True)), refresh=True)
                    data = fetch()
                    body_key = None  # new data: rebuild the body
                    next_at = time.monotonic() + interval
                    remaining, force = interval, False

                # Rebuild the body only when data, view or width changed; otherwise just the header ticks.
                key = (view.tab, console.width)
                if key != body_key:
                    body, body_key = build_tab(data, view.tab, console.width), key

                header = build_header(view.tab, remaining, macro_fetched=data.macro_fetched)
                live.update(build_dashboard(header, body, build_footer(view.tab, live=True)), refresh=True)

                tick_end = time.monotonic() + 1
                while time.monotonic() < tick_end:
                    pressed = keys.read()
                    if pressed in ("q", "Q"):
                        return
                    if pressed in ("r", "R"):
                        force = True
                        break
                    if pressed and handle_key(pressed, view):
                        break  # redraw now from cached data; the countdown keeps running
                    time.sleep(KEY_POLL_SECONDS)
    except KeyboardInterrupt:
        pass
