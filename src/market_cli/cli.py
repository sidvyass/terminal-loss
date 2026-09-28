import argparse
import math
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Literal

from rich.console import Console, RenderableType
from rich.live import Live

from market_cli.config import COUNTRIES, EXTRAS, MIN_REFRESH_SECONDS, REFRESH_SECONDS, TICKERS
from market_cli.data import Quote, fetch_quotes
from market_cli.keys import KeyReader
from market_cli.macro import CountryStats, cache_checked_at, fetch_country_stats
from market_cli.ui import (
    COUNTRY_SORTS,
    SORTS,
    THEME,
    build_countries,
    build_dashboard,
    build_footer,
    build_header,
    build_markets,
    sort_countries,
)

LOADING = "Fetching quotes and country data… (the first run takes about 15s)"
KEY_POLL_SECONDS = 0.05

Tab = Literal["markets", "countries"]


@dataclass
class Snapshot:
    quotes: list[Quote]
    extras: list[Quote]
    countries: list[CountryStats]
    fx: dict[str, Quote]  # currency -> local currency per USD
    macro_fetched: float | None


@dataclass
class View:
    tab: Tab = "markets"
    sort: str = "group"  # Markets sort, cycled with `s`
    country_sort: str = COUNTRY_SORTS[0]  # Countries sort column, cycled with `s`
    selected: str = "India"  # Countries selection, moved with up/down


def fetch() -> Snapshot:
    # Stocks, rates & commodities and FX rates all come from one Yahoo batch; split afterwards.
    fx_symbols = {f"FX {c['currency']}": c["fx"] for c in COUNTRIES.values() if c["fx"]}
    with ThreadPoolExecutor(max_workers=1) as pool:  # macro data (IMF/BIS) loads alongside the quotes
        macro = pool.submit(fetch_country_stats)
        quotes = fetch_quotes({**TICKERS, **EXTRAS, **fx_symbols})
        countries = macro.result()
    n_stocks, n_extras = len(TICKERS), len(EXTRAS)
    stocks = quotes[:n_stocks]
    extras = quotes[n_stocks : n_stocks + n_extras]
    fx = {q.name.removeprefix("FX "): q for q in quotes[n_stocks + n_extras :]}
    return Snapshot(stocks, extras, countries, fx, cache_checked_at())


def build_tab(data: Snapshot, tab: str, view: View, width: int, live: bool = True) -> list[RenderableType]:
    if tab == "markets":
        return build_markets(data.quotes, data.extras, width, view.sort, live)
    if tab == "countries":
        return build_countries(data.countries, data.fx, view.selected, view.country_sort, width)
    return build_tab(data, "markets", view, width, live) + build_tab(data, "countries", view, width, live)


def _cycle(options: list[str], current: str) -> str:
    return options[(options.index(current) + 1) % len(options)]


def handle_key(key: str, view: View, data: Snapshot) -> bool:
    """Apply a view key (tabs, sort, selection); returns True if the view changed. Never refetches."""
    if key == "1":
        view.tab = "markets"
    elif key == "2":
        view.tab = "countries"
    elif key == "\t":
        view.tab = "countries" if view.tab == "markets" else "markets"
    elif key in ("s", "S"):
        if view.tab == "markets":
            view.sort = _cycle(list(SORTS), view.sort)
        else:
            view.country_sort = _cycle(COUNTRY_SORTS, view.country_sort)
    elif key in ("up", "down", "k", "j") and view.tab == "countries":
        # Move through the rows in their displayed (sorted) order; stop at the ends.
        names = [c.name for c in sort_countries(data.countries, view.country_sort)]
        if not names:
            return False
        i = names.index(view.selected) if view.selected in names else 0
        i = max(0, min(len(names) - 1, i + (-1 if key in ("up", "k") else 1)))
        if names[i] == view.selected:
            return False
        view.selected = names[i]
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
        body = build_tab(data, tab, View(), console.width, live=False)
        header = build_header(tab, None, macro_fetched=data.macro_fetched, width=console.width)
        console.print(build_dashboard(header, body, build_footer(tab, live=False)))
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
                    header = build_header(view.tab, None, True, data.macro_fetched, console.width)
                    live.update(build_dashboard(header, body or [], build_footer(view.tab, live=True)), refresh=True)
                    data = fetch()
                    body_key = None  # new data: rebuild the body
                    next_at = time.monotonic() + interval
                    remaining, force = interval, False

                # Rebuild the body only when data, view or width changed; otherwise just the header ticks.
                key = (view.tab, view.sort, view.country_sort, view.selected, console.width)
                if key != body_key:
                    body, body_key = build_tab(data, view.tab, view, console.width), key

                header = build_header(view.tab, remaining, False, data.macro_fetched, console.width)
                live.update(build_dashboard(header, body, build_footer(view.tab, live=True)), refresh=True)

                tick_end = time.monotonic() + 1
                while time.monotonic() < tick_end:
                    pressed = keys.read_key()
                    if pressed in ("q", "Q"):
                        return
                    if pressed in ("r", "R"):
                        force = True
                        break
                    if pressed and handle_key(pressed, view, data):
                        break  # redraw now from cached data; the countdown keeps running
                    time.sleep(KEY_POLL_SECONDS)
    except KeyboardInterrupt:
        pass
