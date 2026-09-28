import pytest

from terminal_loss.api.service import Snapshot
from terminal_loss.data import Quote
from terminal_loss.macro import CountryStats, Stat


def make_snapshot() -> Snapshot:
    return Snapshot(
        quotes=[
            Quote(
                "NVIDIA",
                "NVDA",
                price=230.11,
                prev_close=225.0,
                day_low=224.0,
                day_high=231.0,
                year_low=150.0,
                year_high=240.0,
                volume=10.0,
                avg_volume=12.0,
                history=[1.0, 2.0],
                history_times=["2026-09-28T09:30:00-04:00", "2026-09-28T10:30:00-04:00"],
                timezone="America/New_York",
            ),
            Quote("SpaceX", "SPCX", error="no data"),
        ],
        extras=[Quote("US 10Y", "^TNX", price=5.228, prev_close=5.184)],
        countries=[
            CountryStats(
                name="India",
                currency="INR",
                bis="IN",
                stats={"gdp_growth": Stat(6.5, "2026"), "interest_rate": Stat(5.25, "2026-07-23", stale=True)},
                history={"gdp_growth": [(2025, 6.4), (2026, 6.5)]},
            ),
            CountryStats(name="United States", currency="USD", bis="US", stats={"gdp_growth": Stat(1.9, "2026")}),
        ],
        fx={"INR": Quote("FX INR", "INR=X", price=95.97)},
        macro_fetched=1_790_000_000.0,
    )


@pytest.fixture
def snapshot() -> Snapshot:
    return make_snapshot()
