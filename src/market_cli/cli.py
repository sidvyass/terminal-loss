import argparse
import time

from rich.console import Console, Group
from rich.live import Live

from market_cli.config import FX_SYMBOL, MIN_REFRESH_SECONDS, REFRESH_SECONDS, TICKERS
from market_cli.data import fetch_quotes
from market_cli.macro import fetch_country_stats
from market_cli.ui import build_dashboard


def render(interval: int | None = None) -> Group:
    # Fetch the FX rate in the same batch as the stock quotes.
    quotes = fetch_quotes({**TICKERS, "USD/INR": FX_SYMBOL})
    usd_inr = quotes.pop()
    return build_dashboard(quotes, fetch_country_stats(), usd_inr, interval)


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

    console = Console()
    if args.once:
        console.print(render())
        return

    interval = max(args.interval, MIN_REFRESH_SECONDS)
    try:
        with Live(console=console, screen=True, refresh_per_second=1) as live:
            live.update(f"Fetching quotes for {', '.join(TICKERS.values())}…")
            while True:
                live.update(render(interval))
                time.sleep(interval)
    except KeyboardInterrupt:
        pass
