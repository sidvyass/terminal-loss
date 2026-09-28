"""FastAPI app: `GET /api/snapshot` for the CLI and the web app, `GET /api/history` for web charts,
plus the built web app at `/`."""

import argparse
import logging
import os
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import uvicorn
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles

from terminal_loss.api.schema import snapshot_to_json
from terminal_loss.api.service import HistoryCache, SnapshotCache
from terminal_loss.config import EXTRAS, TICKERS

log = logging.getLogger(__name__)

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8000
# web/dist in a source checkout (src/terminal_loss/api/app.py -> repo root); override with MARKET_WEB_DIST
WEB_DIST = Path(os.environ.get("MARKET_WEB_DIST") or Path(__file__).resolve().parents[3] / "web" / "dist")


# Only configured symbols can be charted, so the endpoint can't be used to proxy arbitrary Yahoo calls.
CHART_SYMBOLS = set(TICKERS.values()) | set(EXTRAS.values())

# The web app loads its own bundle plus Google Fonts; React sets inline styles, hence 'unsafe-inline' for styles.
CSP = "; ".join(
    [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
        "font-src 'self' https://fonts.gstatic.com",
        "img-src 'self' data:",
        "connect-src 'self'",
        "frame-ancestors 'none'",
        "base-uri 'self'",
        "form-action 'self'",
    ]
)
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}
DOCS_PATHS = ("/docs", "/redoc", "/openapi.json")  # Swagger UI loads its assets from a CDN: no CSP there


def create_app(
    cache: SnapshotCache | None = None,
    web_dist: Path | None = WEB_DIST,
    history: HistoryCache | None = None,
    warm: bool = False,
) -> FastAPI:
    """`warm` starts the first snapshot fetch at startup, so the first visitor doesn't wait for all of it."""
    cache = cache or SnapshotCache()
    history = history or HistoryCache()

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        if warm:
            threading.Thread(target=_warm, args=(cache,), daemon=True).start()
        yield

    app = FastAPI(title="Terminal Loss API", lifespan=lifespan)
    app.add_middleware(GZipMiddleware, minimum_size=1024)

    @app.middleware("http")
    async def headers(request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers.update(SECURITY_HEADERS)
        path = request.url.path
        if not path.startswith(DOCS_PATHS):
            response.headers.setdefault("Content-Security-Policy", CSP)
        if path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "no-store")
        elif path.startswith("/assets/"):  # Vite puts a content hash in these file names
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        else:  # index.html and friends: revalidate so a deploy shows up on the next load
            response.headers.setdefault("Cache-Control", "no-cache")
        return response

    @app.get("/api/health")
    def health() -> dict:
        return {"ok": True}

    @app.get("/api/snapshot")
    def snapshot(force: bool = False) -> dict:  # sync endpoint: FastAPI runs the blocking fetch in a thread
        return snapshot_to_json(cache.get(force=force))

    @app.get("/api/history")
    def chart_history(symbol: str, range: Literal["1D", "5D", "1M", "1Y"]) -> list[dict]:
        if symbol not in CHART_SYMBOLS:
            raise HTTPException(404, "unknown symbol")
        try:
            points = history.get(symbol, range)
        except Exception as exc:  # Yahoo failure: the chart shows "No data"
            log.warning("history fetch failed for %s %s: %r", symbol, range, exc)
            raise HTTPException(502, "upstream data source unavailable") from exc
        return [{"t": t, "close": c} for t, c in points]

    if web_dist is not None and (web_dist / "index.html").is_file():
        app.mount("/", StaticFiles(directory=web_dist, html=True), name="web")
    return app


def _warm(cache: SnapshotCache) -> None:
    try:
        cache.get()
    except Exception:
        log.exception("startup snapshot fetch failed; the first request will retry")


def main() -> None:
    parser = argparse.ArgumentParser(prog="market-api", description="Terminal Loss HTTP API and web dashboard")
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", DEFAULT_HOST),
        help=f"interface to bind (default $HOST or {DEFAULT_HOST})",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", DEFAULT_PORT)),
        help=f"port to listen on (default $PORT or {DEFAULT_PORT})",
    )
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(levelname)s:     %(name)s - %(message)s")
    # One process only: the snapshot and history caches live in memory and are shared by every request.
    # Behind a hosting proxy (Render etc.) trust its X-Forwarded-* headers so logs show real client IPs.
    uvicorn.run(create_app(warm=True), host=args.host, port=args.port, proxy_headers=True, forwarded_allow_ips="*")
