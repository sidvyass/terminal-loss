import argparse
import math
import time

from rich.console import Console
from rich.live import Live

from market_cli.config import FX_SYMBOL, MIN_REFRESH_SECONDS, REFRESH_SECONDS, TICKERS
from market_cli.data import Quote, fetch_quotes
from market_cli.keys import KeyReader
from market_cli.macro import CountryStats, fetch_country_stats
from market_cli.ui import THEME, build_body, build_dashboard, build_footer, build_header

LOADING = "Fetching quotes and country data… (the first run takes about 15s)"
KEY_POLL_SECONDS = 0.05

Snapshot = tuple[list[Quote], list[CountryStats], Quote | None]


def fetch() -> Snapshot:
    # Fetch the FX rate in the same batch as the stock quotes.
    quotes = fetch_quotes({**TICKERS, "USD/INR": FX_SYMBOL})
    usd_inr = quotes.pop()
    return quotes, fetch_country_stats(), usd_inr


def main() -> None:
    parser = argparse.ArgumentParser(prog="market", description="Live market dashboard")
    parser.add_argument(
        "--interval",
        type=int,
        default=REFRESH_SECONDS,
        help=f"refresh interval in seconds (default {REFRESH_SECONDS}, min {MIN_REFRESH_SECONDS})",
    )
    parser.add_argument("--once", action="store_true", help="print one snapshot and exit")
    args = parser.parse_args()

    console = Console(theme=THEME)
    try:
        with console.status(LOADING):
            data = fetch()
    except KeyboardInterrupt:
        return

    if args.once:
        body = build_body(*data, console.width)
        console.print(build_dashboard(build_header(None), *body, build_footer(live=False)))
        return

    interval = max(args.interval, MIN_REFRESH_SECONDS)
    footer = build_footer(live=True)
    try:
        with KeyReader() as keys, Live(console=console, screen=True, auto_refresh=False) as live:
            body, body_width = build_body(*data, console.width), console.width
            next_at = time.monotonic() + interval
            force = False
            while True:
                remaining = math.ceil(next_at - time.monotonic())
                if remaining <= 0 or force:
                    live.update(build_dashboard(build_header(None, refreshing=True), *body, footer), refresh=True)
                    data = fetch()
                    body, body_width = build_body(*data, console.width), console.width
                    next_at = time.monotonic() + interval
                    remaining, force = interval, False
                elif console.width != body_width:
                    # Re-layout from cached data so the sparkline column can hide/show.
                    body, body_width = build_body(*data, console.width), console.width

                live.update(build_dashboard(build_header(remaining), *body, footer), refresh=True)

                tick_end = time.monotonic() + 1
                while time.monotonic() < tick_end:
                    key = keys.read()
                    if key in ("q", "Q"):
                        return
                    if key in ("r", "R"):
                        force = True
                        break
                    time.sleep(KEY_POLL_SECONDS)
    except KeyboardInterrupt:
        pass
