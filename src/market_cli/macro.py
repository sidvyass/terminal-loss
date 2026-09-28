"""Country macro stats from the IMF DataMapper and BIS APIs, cached on disk."""

import csv
import io
import json
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import requests
from platformdirs import user_cache_dir

from market_cli.config import COUNTRIES, MACRO_TTL_HOURS

IMF_URL = "https://www.imf.org/external/datamapper/api/v1/{code}"
BIS_URL = "https://stats.bis.org/api/v1/data/WS_CBPOL/D.{areas}"
TIMEOUT = 30  # the IMF API routinely takes ~10s per indicator

# Metric key -> IMF DataMapper indicator code
IMF_INDICATORS = {
    "gdp_growth": "NGDP_RPCH",
    "unemployment": "LUR",
    "inflation": "PCPIPCH",
    "debt_to_gdp": "GGXWDG_NGDP",
}
METRICS = [*IMF_INDICATORS, "interest_rate"]

CACHE_FILE = Path(user_cache_dir("market-cli", appauthor=False)) / "macro.json"
CACHE_VERSION = 2  # v2 adds per-country IMF history
HISTORY_YEARS = 10  # trend covers current year - 10 .. current year


@dataclass
class Stat:
    value: float
    period: str  # year for IMF data, date for BIS
    stale: bool = False


@dataclass
class CountryStats:
    name: str
    currency: str
    bis: str = ""
    stats: dict[str, Stat | None] = field(default_factory=dict)
    history: dict[str, list[tuple[int, float]]] = field(default_factory=dict)  # IMF metrics only


def _fetch_imf(code: str) -> dict[str, dict]:
    """Latest value per country, plus the last HISTORY_YEARS + 1 years from the same response."""
    resp = requests.get(IMF_URL.format(code=code), timeout=TIMEOUT)
    resp.raise_for_status()
    series = resp.json()["values"][code]
    this_year = date.today().year
    data, history = {}, {}
    for country in COUNTRIES.values():
        years = series.get(country["imf"], {})
        # Prefer the current year's (estimated) value, else the latest year available.
        year = str(this_year) if str(this_year) in years else max(years, default=None)
        if year is not None:
            data[country["imf"]] = [years[year], year]
        history[country["imf"]] = [
            [y, years[str(y)]] for y in range(this_year - HISTORY_YEARS, this_year + 1) if str(y) in years
        ]
    return {"data": data, "history": history}


def _fetch_bis() -> dict[str, dict]:
    areas = "+".join(c["bis"] for c in COUNTRIES.values())
    resp = requests.get(
        BIS_URL.format(areas=areas),
        params={"lastNObservations": 1, "format": "csv"},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    result = {}
    for row in csv.DictReader(io.StringIO(resp.text)):
        if row.get("OBS_VALUE"):
            result[row["REF_AREA"]] = [float(row["OBS_VALUE"]), row["TIME_PERIOD"]]
    return {"data": result}


def _load_cache() -> dict:
    try:
        return json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _save_cache(cache: dict) -> None:
    try:
        CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
        CACHE_FILE.write_text(json.dumps(cache), encoding="utf-8")
    except OSError:
        pass  # caching is best-effort


def _refresh(cache: dict) -> dict:
    """Fetch every metric independently; keep the old cached entry for any that fail."""
    fetchers = {key: (lambda code=code: _fetch_imf(code)) for key, code in IMF_INDICATORS.items()}
    fetchers["interest_rate"] = _fetch_bis
    metrics = cache.get("metrics", {})
    with ThreadPoolExecutor(max_workers=len(fetchers)) as pool:
        futures = {key: pool.submit(fetch) for key, fetch in fetchers.items()}
    for key, future in futures.items():
        try:
            metrics[key] = {**future.result(), "fetched_at": time.time()}
        except Exception:
            if key in metrics:
                metrics[key]["stale"] = True
    return {"version": CACHE_VERSION, "countries": _country_codes(), "checked_at": time.time(), "metrics": metrics}


def _country_codes() -> list[str]:
    return sorted(c["imf"] for c in COUNTRIES.values())


def _cache_is_fresh(cache: dict) -> bool:
    return (
        cache.get("version") == CACHE_VERSION
        and cache.get("countries") == _country_codes()  # new countries in config -> refetch
        and time.time() - cache.get("checked_at", 0) <= MACRO_TTL_HOURS * 3600
    )


def cache_checked_at() -> float | None:
    """When the macro cache was last refreshed (epoch seconds), or None if there is no cache."""
    return _load_cache().get("checked_at")


def fetch_country_stats() -> list[CountryStats]:
    cache = _load_cache()
    if not _cache_is_fresh(cache):
        cache = _refresh(cache)
        _save_cache(cache)

    metrics = cache.get("metrics", {})
    results = []
    for name, codes in COUNTRIES.items():
        country = CountryStats(name=name, currency=codes["currency"], bis=codes["bis"])
        for key in METRICS:
            entry = metrics.get(key, {})
            code = codes["bis"] if key == "interest_rate" else codes["imf"]
            point = entry.get("data", {}).get(code)
            country.stats[key] = (
                Stat(value=point[0], period=point[1], stale=entry.get("stale", False)) if point else None
            )
            if key != "interest_rate":  # BIS policy rates have no history in this call
                country.history[key] = [(int(y), v) for y, v in entry.get("history", {}).get(code, [])]
        results.append(country)
    return results
