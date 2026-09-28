from datetime import datetime, time
from zoneinfo import ZoneInfo

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from market_cli.data import Quote
from market_cli.macro import CountryStats, Stat

THEME = Theme(
    {
        "accent": "#f2b84b",
        "up": "#5fd38d",
        "down": "#ff7a7a",
        "symbol": "#7cc7ff",
        "india": "#d6a4ff",
        "dim": "#7f8791",
        "track": "#4a515b",
        "border": "#6b7380",
        "title": "bold #f2f3f5",
        "price": "bold #f2f3f5",
    }
)

NA = Text("N/A", style="dim")
NEW_YORK = ZoneInfo("America/New_York")
SEP = Text(" │ ", style="track")
MINUS = "−"
SPARK_CHARS = "▁▂▃▄▅▆▇█"
BAR_PARTIALS = " ▏▎▍▌▋▊▉"
SPARK_MIN_WIDTH = 120  # below this console width the 5 DAYS column is hidden
ERROR_WIDTH = 14  # max width of an error message in the PRICE cell

# SIMPLE_HEAD plus a rule between rows (drawn in the table's `track` border style).
ROWS_HEAD = box.Box(
    "    \n"
    "    \n"
    " ── \n"
    "    \n"
    " ── \n"
    "    \n"
    "    \n"
    "    \n"
)


def market_status(now: datetime | None = None) -> tuple[str, str]:
    """Regular NYSE/Nasdaq session; ignores exchange holidays. Returns (label, style)."""
    now = (now or datetime.now(NEW_YORK)).astimezone(NEW_YORK)
    if now.weekday() < 5 and time(9, 30) <= now.time() < time(16, 0):
        return "Market open", "up"
    return "Market closed", "accent"


def _direction(value: float | None) -> str:
    if not value:
        return ""
    return "up" if value > 0 else "down"


# ---------------------------------------------------------------- header / footer


def build_header(countdown: int | None, refreshing: bool = False) -> Table:
    label, style = market_status()
    clock = datetime.now(NEW_YORK).strftime("%a %d %b · %H:%M:%S")
    left = Text.assemble((f"● {label}", style), SEP, (f"{clock} ET", ""))
    if refreshing:
        right = Text("refreshing…", style="dim")
    elif countdown is not None:
        right = Text(f"next refresh in {countdown}s", style="dim")
    else:
        right = Text("")
    grid = Table.grid(expand=True)
    grid.add_column(no_wrap=True)
    grid.add_column(justify="right", no_wrap=True)
    grid.add_row(left, right)
    return grid


def build_footer(live: bool) -> Table:
    left = Text("IMF WEO (year shown) · policy rates: BIS", style="dim")
    right = Text("")
    if live:
        right = Text.assemble(("r", "accent"), (" refresh now   ", "dim"), ("q", "accent"), (" quit", "dim"))
    grid = Table.grid(expand=True)
    grid.add_column(no_wrap=True)
    grid.add_column(justify="right", no_wrap=True)
    grid.add_row(left, right)
    return grid


# ---------------------------------------------------------------- stocks panel


def _compact(value: float) -> str:
    """Range-bar label: 612.84, but 82.6k for large values so the column stays narrow."""
    return f"{value / 1000:,.1f}k" if abs(value) >= 10_000 else f"{value:,.2f}"


def _ticker(symbol: str) -> str:
    """Display form of a Yahoo symbol: ^BSESN -> BSESN, BTC-USD -> BTC."""
    return symbol.lstrip("^").removesuffix("-USD")


def _range_bar(value: float | None, low: float | None, high: float | None, width: int = 9) -> Text:
    if value is None or low is None or high is None:
        return NA
    pos = round((value - low) / (high - low) * (width - 1)) if high != low else 0
    pos = max(0, min(width - 1, pos))
    return Text.assemble(
        (_compact(low), "dim"),
        " ",
        ("─" * pos, "track"),
        ("●", "accent"),
        ("─" * (width - 1 - pos), "track"),
        " ",
        (_compact(high), "dim"),
    )


def _spark(values: list[float], n: int = 10) -> str:
    if not values:
        return ""
    if len(values) == 1:
        samples = values * n
    else:
        samples = [values[round(i * (len(values) - 1) / (n - 1))] for i in range(n)]
    lo, hi = min(samples), max(samples)
    if hi == lo:
        return SPARK_CHARS[3] * n
    return "".join(SPARK_CHARS[round((v - lo) / (hi - lo) * 7)] for v in samples)


def _change(value: float | None) -> Text:
    if value is None:
        return NA
    if value == 0:
        return Text("0.00")
    arrow = "▲" if value > 0 else "▼"
    return Text(f"{arrow} {abs(value):,.2f}", style=_direction(value))


def _pct(value: float | None) -> Text:
    if value is None:
        return NA
    if value == 0:
        return Text("0.00%")
    sign = "+" if value > 0 else MINUS
    return Text(f"{sign}{abs(value):,.2f}%", style=_direction(value))


def _name(name: str) -> Text:
    return Text(name, no_wrap=True, overflow="ellipsis")


def build_stocks_panel(quotes: list[Quote], width: int) -> Panel:
    wide = width >= SPARK_MIN_WIDTH
    show_spark = wide
    bar_width = 9 if wide else 7  # narrower range bars leave room for NAME
    table = Table(
        box=ROWS_HEAD,
        header_style="dim",
        border_style="track",
        show_edge=False,
        pad_edge=False,
        show_lines=True,
        expand=True,
    )
    table.add_column("SYMBOL", style="symbol", no_wrap=True)
    # NAME is the only wrappable column, so Rich shrinks it before anything else;
    # its cells are no_wrap Text, so they ellipsize instead.
    table.add_column("NAME", max_width=20)
    table.add_column("PRICE", justify="right", style="price", no_wrap=True)
    table.add_column("CHANGE", justify="right", no_wrap=True)
    table.add_column("%", justify="right", no_wrap=True)
    table.add_column("DAY RANGE", justify="center", no_wrap=True)
    table.add_column("52-WEEK RANGE", justify="center", no_wrap=True)
    if show_spark:
        table.add_column("5 DAYS", justify="right", no_wrap=True)

    for i, q in enumerate(quotes):
        if q.error:
            message = f"error: {q.error}"
            if len(message) > ERROR_WIDTH:  # keep PRICE narrow; it never shrinks
                message = message[: ERROR_WIDTH - 1] + "…"
            error = Text(message, style="down")
            cells = [error, NA, NA, NA, NA] + ([NA] if show_spark else [])
            table.add_row(Text(_ticker(q.symbol), style="bold"), _name(q.name), *cells)
            continue
        row = [
            Text(_ticker(q.symbol), style="bold"),
            _name(q.name),
            Text(f"{q.price:,.2f}", no_wrap=True),
            _change(q.change),
            _pct(q.pct_change),
            _range_bar(q.price, q.day_low, q.day_high, bar_width),
            _range_bar(q.price, q.year_low, q.year_high, bar_width),
        ]
        if show_spark:
            spark = _spark(q.history)
            row.append(Text(spark, style=_direction(q.change)) if spark else NA)
        table.add_row(*row)

    return Panel(table, title=Text("Stocks", style="title"), title_align="left", box=box.ROUNDED, border_style="border")


# ---------------------------------------------------------------- country panel

COUNTRY_ROWS = [
    ("GDP growth", "gdp_growth"),
    ("Unemployment", "unemployment"),
    ("Inflation", "inflation"),
    ("Policy rate", "interest_rate"),
    ("Gov. debt / GDP", "debt_to_gdp"),
]
COUNTRY_STYLES = {"United States": "symbol", "India": "india"}
BAR_WIDTH = 10


def _bar(value: float, max_value: float, style: str, width: int = BAR_WIDTH) -> Text:
    if max_value <= 0:
        return Text(" " * width)
    frac = min(abs(value) / max_value, 1) * width
    full = int(frac)
    part = round((frac - full) * 8)
    if part == 8:
        full, part = full + 1, 0
    bar = "█" * full + (BAR_PARTIALS[part] if part else "")
    return Text(bar.ljust(width), style=style)


def _stat_cell(stat: Stat | None, max_value: float, style: str) -> Text:
    if stat is None:
        return Text.assemble(("N/A".rjust(6), "dim"), "  ", " " * BAR_WIDTH, "  ", ("no IMF series", "dim"))
    value = f"{stat.value:,.3f}".rstrip("0").rstrip(".")  # 3.875 stays, 2.300 -> 2.3
    text = Text.assemble(f"{value}%".rjust(6), "  ", _bar(stat.value, max_value, style), "  ", (stat.period, "dim"))
    if stat.stale:
        text.append(" · cached", style="accent")
    return text


def _currency(country: CountryStats, usd_inr: Quote | None) -> Text:
    text = Text(country.currency)
    if country.currency == "INR" and usd_inr is not None and usd_inr.price is not None:
        text.append(f"  ₹{usd_inr.price:,.2f} per $", style="dim")
    return text


def build_country_panel(countries: list[CountryStats], usd_inr: Quote | None) -> Panel:
    table = Table(
        box=ROWS_HEAD, header_style="dim", border_style="track", show_edge=False, show_lines=True, expand=True
    )
    table.add_column("METRIC", style="bold", no_wrap=True)
    for c in countries:
        table.add_column(Text(c.name.upper(), style=COUNTRY_STYLES.get(c.name, "symbol")), no_wrap=True)

    table.add_row("Currency", *(_currency(c, usd_inr) for c in countries))
    for label, key in COUNTRY_ROWS:
        stats = [c.stats.get(key) for c in countries]
        max_value = max((abs(s.value) for s in stats if s is not None), default=0)
        cells = [_stat_cell(s, max_value, COUNTRY_STYLES.get(c.name, "symbol")) for c, s in zip(countries, stats)]
        table.add_row(label, *cells)

    return Panel(table, title=Text("Country snapshot", style="title"), title_align="left", box=box.ROUNDED, border_style="border")


# ---------------------------------------------------------------- layout


def build_body(
    quotes: list[Quote], countries: list[CountryStats], usd_inr: Quote | None, width: int
) -> tuple[Panel, Panel]:
    return build_stocks_panel(quotes, width), build_country_panel(countries, usd_inr)


def build_dashboard(
    header: RenderableType, stocks: RenderableType, country: RenderableType, footer: RenderableType
) -> Group:
    blank = Text("")
    return Group(header, blank, stocks, blank, country, blank, footer)
