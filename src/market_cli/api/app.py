"""FastAPI app: `GET /api/snapshot` for the CLI and the web app, plus the built web app at `/`."""

import argparse
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from market_cli.api.schema import snapshot_to_json
from market_cli.api.service import SnapshotCache

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
# web/dist in a source checkout (src/market_cli/api/app.py -> repo root); override with MARKET_WEB_DIST
WEB_DIST = Path(os.environ.get("MARKET_WEB_DIST") or Path(__file__).resolve().parents[3] / "web" / "dist")


def create_app(cache: SnapshotCache | None = None, web_dist: Path | None = WEB_DIST) -> FastAPI:
    cache = cache or SnapshotCache()
    app = FastAPI(title="market-cli API")

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/snapshot")
    def snapshot(force: bool = False) -> dict:  # sync endpoint: FastAPI runs the blocking fetch in a thread
        return snapshot_to_json(cache.get(force=force))

    if web_dist is not None and (web_dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    return app


def main() -> None:
    parser = argparse.ArgumentParser(prog="market-api", description="market-cli HTTP API and web dashboard")
    parser.add_argument("--host", default=DEFAULT_HOST, help=f"interface to bind (default {DEFAULT_HOST})")
    parser.add_argument("--port", type=int, default=DEFAULT_PORT, help=f"port to listen on (default {DEFAULT_PORT})")
    args = parser.parse_args()
    uvicorn.run(create_app(), host=args.host, port=args.port)
