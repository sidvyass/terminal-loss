"""JSON shape of a snapshot, shared by the API server and its Python client."""

from dataclasses import asdict, fields
from typing import Any

from market_cli.api.service import Snapshot
from market_cli.config import CENTRAL_BANKS, COUNTRIES, EXTRA_LABELS, GROUPS
from market_cli.data import Quote
from market_cli.macro import CountryStats, Stat

GROUP_OF = {symbol: group for group, members in GROUPS.items() for symbol in members.values()}
QUOTE_FIELDS = {f.name for f in fields(Quote)}


def _country(c: CountryStats, fx: dict[str, Quote]) -> dict[str, Any]:
    codes = COUNTRIES.get(c.name, {})
    rate = 1.0 if c.currency == "USD" else (fx[c.currency].price if c.currency in fx else None)
    return {
        "name": c.name,
        "currency": c.currency,
        "currency_symbol": codes.get("sym") or "",
        "fx_symbol": codes.get("fx"),
        "fx_rate": rate,
        "bis": c.bis,
        "central_bank": CENTRAL_BANKS.get(c.bis),
        "stats": {k: asdict(s) if s else None for k, s in c.stats.items()},
        "history": {k: [[y, v] for y, v in points] for k, points in c.history.items()},
    }


def snapshot_to_json(s: Snapshot) -> dict[str, Any]:
    return {
        # Extras are keyed by display name ("US 10Y"); the Quote's name holds it.
        "quotes": [{**asdict(q), "group": GROUP_OF.get(q.symbol)} for q in s.quotes],
        "extras": [{**asdict(q), "label": EXTRA_LABELS.get(q.name, "")} for q in s.extras],
        "countries": [_country(c, s.fx) for c in s.countries],
        "fx": {ccy: asdict(q) for ccy, q in s.fx.items()},
        "macro_fetched_at": s.macro_fetched,
    }


def _quote_from(d: dict[str, Any]) -> Quote:
    return Quote(**{k: v for k, v in d.items() if k in QUOTE_FIELDS})


def _country_from(d: dict[str, Any]) -> CountryStats:
    return CountryStats(
        name=d["name"],
        currency=d["currency"],
        bis=d.get("bis", ""),
        stats={k: Stat(**s) if s else None for k, s in d.get("stats", {}).items()},
        history={k: [(int(y), v) for y, v in points] for k, points in d.get("history", {}).items()},
    )


def snapshot_from_json(d: dict[str, Any]) -> Snapshot:
    return Snapshot(
        quotes=[_quote_from(q) for q in d["quotes"]],
        extras=[_quote_from(q) for q in d["extras"]],
        countries=[_country_from(c) for c in d["countries"]],
        fx={ccy: _quote_from(q) for ccy, q in d.get("fx", {}).items()},
        macro_fetched=d.get("macro_fetched_at"),
    )
