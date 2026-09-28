import json
from datetime import date
from pathlib import Path

import pytest

from terminal_loss import macro
from terminal_loss.config import COUNTRIES

THIS_YEAR = date.today().year


class FakeResponse:
    def __init__(self, payload: dict | None = None, text: str = "") -> None:
        self._payload = payload
        self.text = text

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


@pytest.fixture(autouse=True)
def cache_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "macro.json"
    monkeypatch.setattr(macro, "CACHE_FILE", path)
    return path


def test_fetch_imf_prefers_current_year_and_keeps_history(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        "values": {
            "NGDP_RPCH": {
                "IND": {str(THIS_YEAR - 11): 1.0, str(THIS_YEAR - 1): 6.4, str(THIS_YEAR): 6.5},
                "USA": {str(THIS_YEAR - 2): 2.1},  # no current-year estimate: latest available
            }
        }
    }
    monkeypatch.setattr(macro.requests, "get", lambda url, timeout: FakeResponse(payload))
    result = macro._fetch_imf("NGDP_RPCH")
    assert result["data"]["IND"] == [6.5, str(THIS_YEAR)]
    assert result["data"]["USA"] == [2.1, str(THIS_YEAR - 2)]
    assert "CHN" not in result["data"]
    assert result["history"]["IND"] == [[THIS_YEAR - 1, 6.4], [THIS_YEAR, 6.5]]  # older than 10 years dropped


def test_fetch_bis_parses_csv(monkeypatch: pytest.MonkeyPatch) -> None:
    csv_text = "REF_AREA,TIME_PERIOD,OBS_VALUE\nUS,2026-09-25,4.375\nIN,2026-09-25,5.25\nCN,2026-09-25,\n"
    monkeypatch.setattr(macro.requests, "get", lambda url, params, timeout: FakeResponse(text=csv_text))
    assert macro._fetch_bis()["data"] == {"US": [4.375, "2026-09-25"], "IN": [5.25, "2026-09-25"]}


def _fake_fetchers(monkeypatch: pytest.MonkeyPatch, fail: set[str] = frozenset()) -> list[str]:
    calls: list[str] = []

    def imf(code: str) -> dict:
        calls.append(code)
        if code in fail:
            raise RuntimeError("imf down")
        return {"data": {"IND": [1.5, str(THIS_YEAR)]}, "history": {"IND": [[THIS_YEAR, 1.5]]}}

    def bis() -> dict:
        calls.append("bis")
        if "bis" in fail:
            raise RuntimeError("bis down")
        return {"data": {"IN": [5.25, "2026-09-25"]}}

    monkeypatch.setattr(macro, "_fetch_imf", imf)
    monkeypatch.setattr(macro, "_fetch_bis", bis)
    return calls


def test_fetch_country_stats_fetches_then_uses_disk_cache(monkeypatch: pytest.MonkeyPatch, cache_file: Path) -> None:
    calls = _fake_fetchers(monkeypatch)
    stats = macro.fetch_country_stats()
    assert [c.name for c in stats] == list(COUNTRIES)
    india = next(c for c in stats if c.name == "India")
    assert india.stats["gdp_growth"].value == 1.5
    assert india.stats["interest_rate"].value == 5.25
    assert india.history["gdp_growth"] == [(THIS_YEAR, 1.5)]
    assert "interest_rate" not in india.history
    assert next(c for c in stats if c.name == "Japan").stats["gdp_growth"] is None
    assert len(calls) == len(macro.IMF_INDICATORS) + 1
    assert cache_file.is_file()
    assert macro.cache_checked_at() is not None

    macro.fetch_country_stats()
    assert len(calls) == len(macro.IMF_INDICATORS) + 1  # fresh cache: no refetch


def test_failed_metric_keeps_previous_value_marked_stale(monkeypatch: pytest.MonkeyPatch, cache_file: Path) -> None:
    _fake_fetchers(monkeypatch)
    macro.fetch_country_stats()
    cache = json.loads(cache_file.read_text(encoding="utf-8"))
    cache["checked_at"] = 0  # expire it
    cache_file.write_text(json.dumps(cache), encoding="utf-8")

    _fake_fetchers(monkeypatch, fail={"bis"})
    india = next(c for c in macro.fetch_country_stats() if c.name == "India")
    assert india.stats["interest_rate"].value == 5.25
    assert india.stats["interest_rate"].stale
    assert not india.stats["gdp_growth"].stale


def test_corrupt_cache_file_is_ignored(monkeypatch: pytest.MonkeyPatch, cache_file: Path) -> None:
    cache_file.write_text("{not json", encoding="utf-8")
    assert macro.cache_checked_at() is None
    _fake_fetchers(monkeypatch)
    assert len(macro.fetch_country_stats()) == len(COUNTRIES)
