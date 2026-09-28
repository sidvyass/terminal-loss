from fastapi.testclient import TestClient

from market_cli.api.app import create_app
from market_cli.api.schema import snapshot_from_json, snapshot_to_json
from market_cli.api.service import Snapshot, SnapshotCache
from market_cli.data import Quote
from market_cli.macro import CountryStats, Stat


def make_snapshot() -> Snapshot:
    return Snapshot(
        quotes=[
            Quote("NVIDIA", "NVDA", price=230.11, prev_close=225.0, volume=10.0, avg_volume=12.0, history=[1.0, 2.0]),
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
            )
        ],
        fx={"INR": Quote("FX INR", "INR=X", price=95.97)},
        macro_fetched=1_790_000_000.0,
    )


def test_schema_round_trip() -> None:
    snap = make_snapshot()
    data = snapshot_to_json(snap)
    assert data["quotes"][0]["group"] == "STOCKS"
    assert data["extras"][0]["label"] == "Treasury yield"
    india = data["countries"][0]
    assert (india["fx_rate"], india["central_bank"], india["currency_symbol"]) == (95.97, "RBI", "₹")
    assert snapshot_from_json(data) == snap


def test_snapshot_endpoint_caches_and_forces() -> None:
    calls = []

    def fetcher() -> Snapshot:
        calls.append(1)
        return make_snapshot()

    client = TestClient(create_app(SnapshotCache(fetcher, max_age=60), web_dist=None))
    assert client.get("/api/health").json() == {"ok": True}

    first = client.get("/api/snapshot")
    assert first.status_code == 200
    assert first.json()["quotes"][0]["symbol"] == "NVDA"
    client.get("/api/snapshot")
    assert len(calls) == 1  # served from cache

    client.get("/api/snapshot", params={"force": "true"})
    assert len(calls) == 2
