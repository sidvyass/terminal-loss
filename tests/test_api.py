from pathlib import Path

import pytest
from conftest import make_snapshot
from fastapi.testclient import TestClient

from terminal_loss.api.app import create_app
from terminal_loss.api.schema import snapshot_from_json, snapshot_to_json
from terminal_loss.api.service import HistoryCache, Snapshot, SnapshotCache


def test_schema_round_trip(snapshot: Snapshot) -> None:
    data = snapshot_to_json(snapshot)
    assert data["quotes"][0]["group"] == "STOCKS"
    assert data["quotes"][0]["history_5d"][1] == {"t": "2026-09-28T10:30:00-04:00", "close": 2.0}
    assert "history" not in data["quotes"][0]
    assert data["extras"][0]["label"] == "Treasury yield"
    india, us = data["countries"]
    assert (india["fx_rate"], india["central_bank"], india["currency_symbol"]) == (95.97, "RBI", "₹")
    assert (us["fx_rate"], us["central_bank"]) == (1.0, "Fed")
    assert snapshot_from_json(data) == snapshot


def test_snapshot_endpoint_caches_and_forces() -> None:
    calls = []

    def fetcher() -> Snapshot:
        calls.append(1)
        return make_snapshot()

    client = TestClient(create_app(SnapshotCache(fetcher, max_age=60, min_force_age=0), web_dist=None))
    assert client.get("/api/health").json() == {"ok": True}

    first = client.get("/api/snapshot")
    assert first.status_code == 200
    assert first.json()["quotes"][0]["symbol"] == "NVDA"
    client.get("/api/snapshot")
    assert len(calls) == 1  # served from cache

    client.get("/api/snapshot", params={"force": "true"})
    assert len(calls) == 2


def test_snapshot_force_is_rate_limited() -> None:
    calls = []

    def fetcher() -> Snapshot:
        calls.append(1)
        return make_snapshot()

    client = TestClient(create_app(SnapshotCache(fetcher, max_age=60, min_force_age=60), web_dist=None))
    for _ in range(5):
        assert client.get("/api/snapshot", params={"force": "true"}).status_code == 200
    assert len(calls) == 1


def test_history_endpoint() -> None:
    calls = []

    def fetcher(symbol: str, range_: str) -> list[tuple[str, float]]:
        calls.append((symbol, range_))
        if symbol == "SPCX":
            raise RuntimeError("rate limited: secret upstream detail")
        return [("2026-09-28T09:30:00-04:00", 229.5), ("2026-09-28T09:35:00-04:00", 230.1)]

    client = TestClient(create_app(SnapshotCache(make_snapshot), web_dist=None, history=HistoryCache(fetcher)))
    resp = client.get("/api/history", params={"symbol": "NVDA", "range": "1D"})
    assert resp.status_code == 200
    assert resp.json()[1] == {"t": "2026-09-28T09:35:00-04:00", "close": 230.1}
    client.get("/api/history", params={"symbol": "NVDA", "range": "1D"})
    assert calls == [("NVDA", "1D")]  # served from cache

    assert client.get("/api/history", params={"symbol": "EVIL", "range": "1D"}).status_code == 404
    assert client.get("/api/history", params={"symbol": "NVDA", "range": "10Y"}).status_code == 422
    assert client.get("/api/history", params={"symbol": "NVDA"}).status_code == 422
    failed = client.get("/api/history", params={"symbol": "SPCX", "range": "1M"})
    assert failed.status_code == 502
    assert "secret" not in failed.text  # upstream error details stay in the server log


@pytest.fixture
def web_dist(tmp_path: Path) -> Path:
    (tmp_path / "assets").mkdir()
    (tmp_path / "index.html").write_text("<!doctype html><title>Terminal Loss</title>", encoding="utf-8")
    (tmp_path / "assets" / "index-abc123.js").write_text("console.log(1);" * 200, encoding="utf-8")
    return tmp_path


def test_serves_web_app_with_headers(web_dist: Path) -> None:
    client = TestClient(create_app(SnapshotCache(make_snapshot), web_dist=web_dist))

    index = client.get("/")
    assert index.status_code == 200
    assert "Terminal Loss" in index.text
    assert index.headers["cache-control"] == "no-cache"
    assert "default-src 'self'" in index.headers["content-security-policy"]
    assert index.headers["x-content-type-options"] == "nosniff"
    assert index.headers["x-frame-options"] == "DENY"

    asset = client.get("/assets/index-abc123.js", headers={"Accept-Encoding": "gzip"})
    assert asset.status_code == 200
    assert "immutable" in asset.headers["cache-control"]
    assert asset.headers["content-encoding"] == "gzip"

    assert client.get("/nope").status_code == 404


def test_api_headers_and_docs_csp() -> None:
    client = TestClient(create_app(SnapshotCache(make_snapshot), web_dist=None))
    snap = client.get("/api/snapshot")
    assert snap.headers["cache-control"] == "no-store"
    assert "content-security-policy" in snap.headers
    docs = client.get("/docs")
    assert docs.status_code == 200
    assert "content-security-policy" not in docs.headers  # Swagger UI loads its assets from a CDN


def test_warm_start_fetches_once_in_background() -> None:
    calls = []

    def fetcher() -> Snapshot:
        calls.append(1)
        return make_snapshot()

    cache = SnapshotCache(fetcher, max_age=60)
    with TestClient(create_app(cache, web_dist=None, warm=True)) as client:
        assert client.get("/api/snapshot").status_code == 200
    assert len(calls) == 1  # the request waited on (or reused) the warm-up fetch
