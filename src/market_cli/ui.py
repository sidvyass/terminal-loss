from datetime import datetime, time
from zoneinfo import ZoneInfo

from rich.console import Group
from rich.table import Table
from rich.text import Text

from market_cli.data import Quote
from market_cli.macro import CountryStats, Stat

NA = Text("N/A", style="dim")
NEW_YORK = ZoneInfo("America/New_York")


def _num(value: float | None) -> Text:
    return NA if value is None else Text(f"{value:,.2f}")


def _range(low: float | None, high: float | None) -> Text:
    if low is None or high is None:
        return NA
    return Text(f"{low:,.2f} – {high:,.2f}")


def _signed(value: float | None, suffix: str = "") -> Text:
    if value is None:
        return NA
    if value > 0:
        return Text(f"▲ {value:,.2f}{suffix}", style="green")
    if value < 0:
        return Text(f"▼ {abs(value):,.2f}{suffix}", style="red")
    return Text(f"  0.00{suffix}")


def market_status(now: datetime | None = None) -> str:
    """Regular NYSE/Nasdaq session; ignores exchange holidays."""
    now = (now or datetime.now(NEW_YORK)).astimezone(NEW_YORK)
    if now.weekday() < 5 and time(9, 30) <= now.time() < time(16, 0):
        return "[green]Market open[/green]"
    return "[yellow]Market closed[/yellow]"


def build_table(quotes: list[Quote]) -> Table:
    table = Table(title="Market Dashboard", title_style="bold")
    table.add_column("Name", style="bold")
    table.add_column("Symbol", style="cyan")
    table.add_column("Price", justify="right")
    table.add_column("Change", justify="right")
    table.add_column("% Change", justify="right")
    table.add_column("Day Range", justify="right", no_wrap=True)
    table.add_column("52w Range", justify="right", no_wrap=True)

    for q in quotes:
        if q.error:
            table.add_row(q.name, q.symbol, Text(f"error: {q.error}", style="red"), NA, NA, NA, NA)
            continue
        table.add_row(
            q.name,
            q.symbol,
            _num(q.price),
            _signed(q.change),
            _signed(q.pct_change, "%"),
            _range(q.day_low, q.day_high),
            _range(q.year_low, q.year_high),
        )
    return table


COUNTRY_ROWS = [
    ("GDP growth (annual)", "gdp_growth"),
    ("Unemployment rate", "unemployment"),
    ("Inflation rate", "inflation"),
    ("Interest rate", "interest_rate"),
    ("Gov. debt to GDP", "debt_to_gdp"),
]


def _stat(stat: Stat | None) -> Text:
    if stat is None:
        return NA
    value = f"{stat.value:,.3f}".rstrip("0").rstrip(".")  # 3.875 stays, 2.300 -> 2.3
    text = Text(f"{value}%")
    text.append(f"  ({stat.period}{', cached' if stat.stale else ''})", style="dim")
    return text


def _currency(country: CountryStats, usd_inr: Quote | None) -> Text:
    text = Text(country.currency)
    if country.currency == "INR" and usd_inr is not None and usd_inr.price is not None:
        text.append(f"  (₹{usd_inr.price:,.2f} per $)", style="dim")
    return text


def build_country_table(countries: list[CountryStats], usd_inr: Quote | None) -> Table:
    table = Table(title="Country Snapshot", title_style="bold")
    table.add_column("Metric", style="bold")
    for c in countries:
        table.add_column(c.name, justify="right", no_wrap=True)

    table.add_row("Currency", *(_currency(c, usd_inr) for c in countries))
    for label, key in COUNTRY_ROWS:
        table.add_row(label, *(_stat(c.stats.get(key)) for c in countries))
    return table


def build_dashboard(
    quotes: list[Quote],
    countries: list[CountryStats],
    usd_inr: Quote | None,
    interval: int | None = None,
) -> Group:
    updated = datetime.now().strftime("%H:%M:%S")
    footer = f"Last updated {updated}  •  {market_status()}"
    if interval:
        footer += f"  •  refreshing every {interval}s  •  Ctrl+C to quit"
    sources = "Macro data: IMF World Economic Outlook (year shown) • policy rates: BIS"
    return Group(
        build_table(quotes),
        Text(""),
        build_country_table(countries, usd_inr),
        Text(sources, style="dim"),
        Text.from_markup(footer),
    )
