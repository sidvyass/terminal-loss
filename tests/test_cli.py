import pytest
from rich.console import Console

from terminal_loss.api.service import Snapshot
from terminal_loss.cli import View, build_tab, handle_key
from terminal_loss.keys import KeyReader
from terminal_loss.ui import THEME, build_dashboard, build_footer, build_header


def test_tab_keys(snapshot: Snapshot) -> None:
    view = View()
    assert handle_key("2", view, snapshot) and view.tab == "countries"
    assert handle_key("\t", view, snapshot) and view.tab == "markets"
    assert handle_key("1", view, snapshot) and view.tab == "markets"
    assert not handle_key("x", view, snapshot)


def test_sort_key_cycles_the_current_tab(snapshot: Snapshot) -> None:
    view = View()
    handle_key("s", view, snapshot)
    assert view.sort == "pct"
    view.tab = "countries"
    first = view.country_sort
    handle_key("S", view, snapshot)
    assert view.country_sort != first
    assert view.sort == "pct"


def test_selection_moves_in_display_order_and_stops_at_ends(snapshot: Snapshot) -> None:
    view = View(tab="countries", country_sort="name")  # India, United States
    assert handle_key("down", view, snapshot) and view.selected == "United States"
    assert not handle_key("j", view, snapshot)  # already last
    assert handle_key("k", view, snapshot) and view.selected == "India"
    assert not handle_key("up", view, snapshot)
    assert not handle_key("down", View(tab="markets"), snapshot)  # markets has no country selection


@pytest.mark.parametrize("tab", ["markets", "countries", "all"])
@pytest.mark.parametrize("width", [80, 160])
def test_dashboard_renders(snapshot: Snapshot, tab: str, width: int) -> None:
    console = Console(theme=THEME, width=width, record=True, force_terminal=False)
    body = build_tab(snapshot, tab, View(), width, live=False)
    header = build_header(tab, None, macro_fetched=snapshot.macro_fetched, width=width)
    console.print(build_dashboard(header, body, build_footer(tab, live=False)))
    text = console.export_text()
    if tab != "countries":
        assert "NVDA" in text
    if tab != "markets":
        assert "India" in text


def test_key_reader_decodes_posix_input() -> None:
    reader = KeyReader()
    reader._pending = "\x1b[Aq\x1bOB\x1b[Cx\x1b"
    keys = [reader._next_pending() for _ in range(6)]
    assert keys == ["up", "q", "down", None, "x", None]
    assert reader._next_pending() is None
