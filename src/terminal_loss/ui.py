from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from rich import box
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.theme import Theme

from terminal_loss.config import CENTRAL_BANKS, COUNTRIES, EXTRA_LABELS, GROUPS, MACRO_TTL_HOURS
from terminal_loss.data import Quote
from terminal_loss.macro import HISTORY_YEARS, CountryStats, Stat

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
        "tab_on": "bold #0d0f12 on #d7dae0",
        "tab_off": "#aab1bb",
        "emph": "#d7dae0",
        "selected": "on #1d2430",
    }
)

NA = Text("N/A", style="dim")
NEW_YORK = ZoneInfo("America/New_York")
SEP = Text(" │ ", style="track")
MINUS = "−"
SPARK_CHARS = "▁▂▃▄▅▆▇█"
BAR_PARTIALS = " ▏▎▍▌▋▊▉"
SPARK_MIN_WIDTH = 120  # below this console width the 5 DAYS column is hidden
VOL_MIN_WIDTH = 105  # ...and below this, the VOL column too
EXTRAS_MIN_WIDTH = 135  # below this, the Rates & commodities panel wraps to 3 columns
HIGH_VOLUME = 1.5  # VOL ratio at or above this is highlighted
ERROR_WIDTH = 14  # max width of an error message in the PRICE cell

# SIMPLE_HEAD plus a rule between rows (drawn in the table's `track` border style).
ROWS_HEAD = box.Box("    \n    \n ── \n    \n ── \n    \n    \n    \n")


# name -> (timezone, open, close, tz label). Holidays are ignored.
SESSIONS: dict[str, tuple[ZoneInfo, time, time, str]] = {
    "NYSE": (NEW_YORK, time(9, 30), time(16, 0), "ET"),
    "BSE": (ZoneInfo("Asia/Kolkata"), time(9, 15), time(15, 30), "IST"),
}


def session_status(exchange: str, now: datetime | None = None) -> tuple[bool, str]:
    """(is_open, local time "HH:MM TZ") for an exchange's regular Mon-Fri session."""
    tz, open_at, close_at, label = SESSIONS[exchange]
    local = (now or datetime.now(tz)).astimezone(tz)
    is_open = local.weekday() < 5 and open_at <= local.time() < close_at
    return is_open, f"{local:%H:%M} {label}"


def _panel(content: RenderableType, title: str) -> Panel:
    """Rounded panel with a blank line above and below the content, so titles don't crowd it."""
    return Panel(
        content,
        title=Text(title, style="title"),
        title_align="left",
        box=box.ROUNDED,
        border_style="border",
        padding=(1, 1),
    )


def _direction(value: float | None) -> str:
    if not value:
        return ""
    return "up" if value > 0 else "down"


# ---------------------------------------------------------------- header / footer

TABS = [("markets", "1", "Markets"), ("countries", "2", "Countries")]


def _tab_labels(tab: str) -> Text:
    text = Text()
    for name, key, label in TABS:
        text.append(f" {key} {label} ", style="tab_on" if name == tab else "tab_off")
    return text


def _refresh_text(countdown: int | None, refreshing: bool, compact: bool = False) -> Text:
    if refreshing:
        return Text("refreshing…", style="dim")
    if countdown is not None:
        return Text(f"↻ {countdown}s" if compact else f"next refresh in {countdown}s", style="dim")
    return Text("")


def _markets_status() -> Text:
    text = Text()
    for i, exchange in enumerate(SESSIONS):
        is_open, clock = session_status(exchange)
        style = "up" if is_open else "accent"
        if i:
            text.append_text(SEP)
        text.append(f"● {exchange} {'open' if is_open else 'closed'}", style=style)
        text.append(f"  {clock}", style="dim")
    return text


def _countries_status(compact: bool = False) -> Text:
    year = date.today().year
    if compact:
        return Text(f"IMF WEO {year} · BIS · FX live", style="dim")
    return Text(f"IMF WEO estimates for {year} · policy rates BIS · FX live", style="dim")


def build_header(
    tab: str,
    countdown: int | None,
    refreshing: bool = False,
    macro_fetched: float | None = None,
    width: int | None = None,
) -> Table:
    """Status line. `tab` is "markets", "countries" or "all" (--once: no tab labels)."""
    width = width or 200
    if tab == "all":
        left = _markets_status()
    else:
        status = _markets_status() if tab == "markets" else _countries_status(compact=width < 110)
        left = Text.assemble(_tab_labels(tab), SEP, status)

    right = _refresh_text(countdown, refreshing, compact=width < SPARK_MIN_WIDTH)
    if tab == "countries" and macro_fetched is not None:
        fetched = datetime.fromtimestamp(macro_fetched).strftime("%H:%M")
        prefix = "" if width < 140 else f"macro cache {MACRO_TTL_HOURS}h · "
        cache = Text(f"{prefix}fetched {fetched}", style="dim")
        right = Text.assemble(cache, "   ", right) if right.plain else cache

    grid = Table.grid(expand=True)
    grid.add_column(no_wrap=True)
    grid.add_column(justify="right", no_wrap=True)
    grid.add_row(left, right)
    return grid


SOURCES = {
    "markets": "Yahoo Finance · 5-day hourly closes",
    "countries": "IMF WEO (year shown) · policy rates: BIS",
}
KEY_HINTS = {
    "markets": [("1 2", "tabs"), ("s", "sort"), ("r", "refresh now"), ("q", "quit")],
    "countries": [("1 2", "tabs"), ("↑↓", "select country"), ("s", "sort column"), ("r", "refresh now"), ("q", "quit")],
}


def build_footer(tab: str, live: bool) -> Table:
    """Sources on the left; key hints on the right (live mode only)."""
    if tab == "all":
        left = Text(" · ".join(SOURCES.values()), style="dim")
    else:
        left = Text(SOURCES[tab], style="dim")
    right = Text("")
    if live and tab in KEY_HINTS:
        for i, (key, label) in enumerate(KEY_HINTS[tab]):
            right.append(("   " if i else "") + key, style="accent")
            right.append(f" {label}", style="dim")
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


SORTS = {"group": "group", "pct": "% change", "name": "name"}  # cycle order for `s`
GROUP_OF = {symbol: group for group, members in GROUPS.items() for symbol in members.values()}


def _volume(q: Quote) -> Text:
    if not q.volume or not q.avg_volume:  # indices report 0 volume
        return NA
    ratio = q.volume / q.avg_volume
    return Text(f"{ratio:.1f}×", style="accent" if ratio >= HIGH_VOLUME else "dim", no_wrap=True)


def sort_quotes(quotes: list[Quote], sort: str) -> list[Quote]:
    if sort == "pct":  # descending; errors / missing last
        return sorted(quotes, key=lambda q: (q.pct_change is None, -(q.pct_change or 0)))
    if sort == "name":
        return sorted(quotes, key=lambda q: q.name.lower())
    return quotes  # "group": config order, which is grouped


def build_stocks_panel(quotes: list[Quote], width: int, sort: str = "group") -> Panel:
    wide = width >= SPARK_MIN_WIDTH
    show_spark = wide
    show_vol = width >= VOL_MIN_WIDTH
    bar_width = 9 if wide else 7 if show_vol else 6  # narrower range bars leave room for NAME
    table = Table(
        box=ROWS_HEAD,
        header_style="dim",
        border_style="track",
        show_edge=False,
        pad_edge=False,
        expand=True,
    )
    if show_vol:
        table.caption = f"VOL = today's volume vs 3-month average, amber at {HIGH_VOLUME}× or more"
        table.caption_style = "dim"
        table.caption_justify = "left"
    # SYMBOL and NAME are the only wrappable columns, so Rich shrinks them before anything else.
    # Their data cells are no_wrap Text (they ellipsize); only group labels wrap onto two lines.
    table.add_column("SYMBOL", style="symbol")
    table.add_column("NAME", max_width=20)
    table.add_column("PRICE", justify="right", style="price", no_wrap=True)
    table.add_column("CHANGE", justify="right", no_wrap=True)
    table.add_column("%", justify="right", no_wrap=True)
    table.add_column("DAY RANGE", justify="center", no_wrap=True)
    table.add_column("52-WEEK RANGE", justify="center", no_wrap=True)
    if show_vol:
        table.add_column(Text("VOL", style="accent"), justify="right", no_wrap=True)
    if show_spark:
        table.add_column("5 DAYS", justify="right", no_wrap=True)

    rows = sort_quotes(quotes, sort)
    grouped = sort == "group"
    for i, q in enumerate(rows):
        group = GROUP_OF.get(q.symbol)
        if grouped and (i == 0 or GROUP_OF.get(rows[i - 1].symbol) != group):
            if i:
                table.add_row()  # blank line between groups
            label = Text(group or "", style="dim")
            label.stylize("bold")
            table.add_row(label, end_section=True)  # section heading, ruled off from its rows
        # Rule under each row, except the last row overall and a group's last row (a blank line follows).
        group_ends = grouped and i + 1 < len(rows) and GROUP_OF.get(rows[i + 1].symbol) != group
        last = i == len(rows) - 1 or group_ends
        if q.error:
            message = f"error: {q.error}"
            if len(message) > ERROR_WIDTH:  # keep PRICE narrow; it never shrinks
                message = message[: ERROR_WIDTH - 1] + "…"
            error = Text(message, style="down")
            cells = [error, NA, NA, NA, NA] + [NA] * (show_vol + show_spark)
            table.add_row(
                Text(_ticker(q.symbol), style="bold", no_wrap=True, overflow="ellipsis"),
                _name(q.name),
                *cells,
                end_section=not last,
            )
            continue
        row = [
            Text(_ticker(q.symbol), style="bold", no_wrap=True, overflow="ellipsis"),
            _name(q.name),
            Text(f"{q.price:,.2f}", no_wrap=True),
            _change(q.change),
            _pct(q.pct_change),
            _range_bar(q.price, q.day_low, q.day_high, bar_width),
            _range_bar(q.price, q.year_low, q.year_high, bar_width),
        ]
        if show_vol:
            row.append(_volume(q))
        if show_spark:
            spark = _spark(q.history)
            row.append(Text(spark, style=_direction(q.change)) if spark else NA)
        table.add_row(*row, end_section=not last)

    return _panel(table, "Stocks")


def build_breadth(quotes: list[Quote], sort: str, live: bool) -> Table:
    moved = [q for q in quotes if not q.error and q.pct_change]
    ups = sum(q.pct_change > 0 for q in moved)
    left = Text.assemble(("Breadth  ", "dim"), (f"{ups} ▲", "up"), "  ", (f"{len(moved) - ups} ▼", "down"))
    if moved:
        best = max(moved, key=lambda q: q.pct_change)
        worst = min(moved, key=lambda q: q.pct_change)
        left.append_text(SEP)
        for i, (label, q) in enumerate([("Best", best), ("Worst", worst)]):
            left.append(("   " if i else "") + f"{label}  ", style="dim")
            left.append(f"{_ticker(q.symbol)} ")
            left.append_text(_pct(q.pct_change))
    right = Text.assemble(("sorted by ", "dim"), (SORTS[sort], "emph"))
    if live:
        right.append(" · s to cycle", style="dim")
    grid = Table.grid(expand=True)
    grid.add_column(no_wrap=True)
    grid.add_column(justify="right", no_wrap=True)
    grid.add_row(left, right)
    return grid


# ---------------------------------------------------------------- rates & commodities


def _extra_cell(q: Quote) -> Text:
    key = Text(q.name, style="symbol")
    key.stylize("bold")
    text = Text.assemble(key, " ", (EXTRA_LABELS.get(q.name, ""), "dim"), "\n")
    if q.error or q.price is None:
        text.append_text(NA)
        return text
    price = f"{q.price:.3f}%" if q.symbol == "^TNX" else f"{q.price:,.2f}"  # ^TNX is quoted as the yield
    text.append(price, style="price")
    style = _direction(q.pct_change)
    if q.pct_change is not None:
        arrow = "▲" if q.pct_change > 0 else "▼" if q.pct_change < 0 else " "
        text.append(f" {arrow} {abs(q.pct_change):.2f}%", style=style)
    spark = _spark(q.history, 8)
    if spark:
        text.append(f" {spark}", style=style)
    return text


def build_extras_panel(extras: list[Quote], width: int) -> Panel:
    ncols = len(extras) if width >= EXTRAS_MIN_WIDTH else 3
    grid = Table.grid(expand=True, padding=(0, 1))
    for _ in range(ncols):
        grid.add_column(ratio=1, no_wrap=True)
    cells = [_extra_cell(q) for q in extras]
    for i in range(0, len(cells), ncols):
        row = cells[i : i + ncols]
        if i:
            grid.add_row(*[""] * ncols)  # spacer between wrapped rows
        grid.add_row(*row, *[""] * (ncols - len(row)))
    return _panel(grid, "Rates & commodities")


# ---------------------------------------------------------------- countries tab

# metric key -> (table header, trend label)
COUNTRY_METRICS = {
    "gdp_growth": ("GDP GROWTH", "GDP growth"),
    "unemployment": ("UNEMPLOYMENT", "Unemployment"),
    "inflation": ("INFLATION", "Inflation"),
    "interest_rate": ("POLICY RATE", "Policy rate"),
    "debt_to_gdp": ("DEBT / GDP", "Gov. debt / GDP"),
}
COUNTRY_SORTS = [*COUNTRY_METRICS, "name"]  # cycle order for `s`; metrics sort descending
COUNTRY_BAR_WIDTH = 7
COUNTRY_BARS_MIN_WIDTH = 130  # below this the country table drops its bars


def country_style(name: str) -> str:
    return "india" if name == "India" else "symbol"


def _fmt_pct(value: float) -> str:
    return f"{value:,.3f}".rstrip("0").rstrip(".") + "%"  # 3.875 stays, 2.300 -> 2.3


def _bar(value: float, max_value: float, style: str, width: int = COUNTRY_BAR_WIDTH) -> Text:
    if max_value <= 0:
        return Text(" " * width)
    frac = min(abs(value) / max_value, 1) * width
    full = int(frac)
    part = round((frac - full) * 8)
    if part == 8:
        full, part = full + 1, 0
    bar = "█" * full + (BAR_PARTIALS[part] if part else "")
    return Text(bar.ljust(width), style=style)


def sort_countries(countries: list[CountryStats], sort_key: str) -> list[CountryStats]:
    if sort_key == "name":
        return sorted(countries, key=lambda c: c.name)
    # Descending by value; countries with no value go last.
    return sorted(
        countries,
        key=lambda c: (c.stats.get(sort_key) is None, -(c.stats[sort_key].value if c.stats.get(sort_key) else 0)),
    )


def _ccy_cell(country: CountryStats, fx: dict[str, Quote]) -> Text:
    sym = COUNTRIES.get(country.name, {}).get("sym") or ""
    text = Text(country.currency + " ")
    if country.currency == "USD":
        text.append(f"{sym}1.00", style="dim")
    elif (q := fx.get(country.currency)) is not None and q.price is not None:
        text.append(f"{sym}{q.price:,.2f}", style="dim")
    else:
        text.append("N/A", style="dim")
    return text


def _metric_cell(stat: Stat | None, col_max: float, style: str, bar_width: int) -> Text:
    if stat is None:
        return Text("N/A".rjust(6), style="dim")
    text = Text(_fmt_pct(stat.value).rjust(6))
    text.append("*" if stat.stale else " ", style="accent")
    if bar_width:
        text.append("  ")
        text.append_text(_bar(stat.value, col_max, style, bar_width))
    return text


def build_country_table(
    countries: list[CountryStats], fx: dict[str, Quote], selected: str, sort_key: str, width: int
) -> Panel:
    bar_width = COUNTRY_BAR_WIDTH if width >= COUNTRY_BARS_MIN_WIDTH else 0
    table = Table(
        box=ROWS_HEAD,
        header_style="dim",
        border_style="track",
        show_edge=False,
        pad_edge=False,
        expand=True,
        caption="Bars scale to the highest value in each column · * cached · N/A = no IMF series",
        caption_style="dim",
        caption_justify="left",
    )

    def header(label: str, key: str) -> Text:
        return Text(f"{label} ▼", style="accent") if key == sort_key else Text(label)

    table.add_column(header("  COUNTRY", "name"), no_wrap=True)  # "▌ " selection marker + name
    table.add_column("CCY · PER $", no_wrap=True)
    for key, (label, _) in COUNTRY_METRICS.items():
        table.add_column(header(label, key), no_wrap=True, ratio=1)  # only metric columns absorb extra width

    col_max = {
        key: max((abs(s.value) for c in countries if (s := c.stats.get(key)) is not None), default=0)
        for key in COUNTRY_METRICS
    }
    rows = sort_countries(countries, sort_key)
    for i, c in enumerate(rows):
        is_selected = c.name == selected
        cells = [
            _metric_cell(c.stats.get(key), col_max[key], "accent" if key == sort_key else "symbol", bar_width)
            for key in COUNTRY_METRICS
        ]
        name = Text(c.name, style="bold")
        name.pad_left(2)
        if is_selected:
            name.stylize("accent", 0, 1)
            name.plain = "▌" + name.plain[1:]
        table.add_row(
            name,
            _ccy_cell(c, fx),
            *cells,
            style="selected" if is_selected else None,
            end_section=i < len(rows) - 1,
        )
    return _panel(table, "Countries")


def _trend_cell(country: CountryStats, key: str) -> Text:
    label = COUNTRY_METRICS[key][1]
    text = Text(label, style="dim")
    text.append("\n")
    stat = country.stats.get(key)
    if stat is None:
        text.append("N/A", style="dim")
        text.append("\nno IMF series", style="dim")
        return text
    value = Text(_fmt_pct(stat.value))
    value.stylize("bold")
    text.append_text(value)
    values = [v for _, v in country.history.get(key, [])]
    if len(values) > 1:
        text.append("  " + _spark(values, 11), style=country_style(country.name))
    text.append("\n")
    if stat.stale:
        text.append("cached", style="accent")
    elif key == "interest_rate":
        text.append(f"{CENTRAL_BANKS.get(country.bis, 'central bank')} · {stat.period}", style="dim")
    else:
        text.append("IMF WEO", style="dim")
    return text


def build_trend_panel(country: CountryStats) -> Panel:
    grid = Table.grid(expand=True, padding=(0, 1))
    for _ in COUNTRY_METRICS:
        grid.add_column(ratio=1, no_wrap=True)
    grid.add_row(*(_trend_cell(country, key) for key in COUNTRY_METRICS))
    this_year = date.today().year
    note = Text(f"{this_year - HISTORY_YEARS} → {this_year} · same IMF DataMapper call", style="dim")
    return _panel(Group(grid, Text(""), note), f"{country.name} · 10-year trend")


# ---------------------------------------------------------------- layout


def build_markets(
    quotes: list[Quote], extras: list[Quote], width: int, sort: str = "group", live: bool = True
) -> list[RenderableType]:
    return [
        build_breadth(quotes, sort, live),
        build_stocks_panel(quotes, width, sort),
        build_extras_panel(extras, width),
    ]


def build_countries(
    countries: list[CountryStats], fx: dict[str, Quote], selected: str, sort_key: str, width: int
) -> list[RenderableType]:
    body: list[RenderableType] = [build_country_table(countries, fx, selected, sort_key, width)]
    current = next((c for c in countries if c.name == selected), None)
    if current is not None:
        body.append(build_trend_panel(current))
    return body


def build_dashboard(header: RenderableType, body: list[RenderableType], footer: RenderableType) -> Group:
    blank = Text("")
    parts: list[RenderableType] = [header, blank]
    for i, part in enumerate(body):
        parts += [blank, part] if i else [part]
    return Group(*parts, blank, footer)
