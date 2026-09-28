"""Python client for the API; starts an in-process server when none is reachable."""

import socket
import threading
import time

import requests
import uvicorn

from market_cli.api.schema import snapshot_from_json
from market_cli.api.service import Snapshot

HEALTH_TIMEOUT = 2
SNAPSHOT_TIMEOUT = 90  # a cold fetch waits on the IMF API, which can take ~10s per indicator
STARTUP_TIMEOUT = 10


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.base_url = base_url.rstrip("/")
        self._session = requests.Session()

    def healthy(self) -> bool:
        try:
            return self._session.get(f"{self.base_url}/api/health", timeout=HEALTH_TIMEOUT).ok
        except requests.RequestException:
            return False

    def snapshot(self, force: bool = False) -> Snapshot:
        resp = self._session.get(
            f"{self.base_url}/api/snapshot",
            params={"force": "true"} if force else None,
            timeout=SNAPSHOT_TIMEOUT,
        )
        resp.raise_for_status()
        return snapshot_from_json(resp.json())


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _start_embedded() -> str:
    """Run the API on a free local port in a daemon thread; returns its base URL."""
    from market_cli.api.app import create_app  # only needed when no server is running

    port = _free_port()
    config = uvicorn.Config(create_app(web_dist=None), host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    threading.Thread(target=server.run, daemon=True).start()
    deadline = time.monotonic() + STARTUP_TIMEOUT
    while not server.started:
        if time.monotonic() > deadline:
            raise RuntimeError("embedded API server did not start")
        time.sleep(0.05)
    return f"http://127.0.0.1:{port}"


def connect(url: str) -> ApiClient:
    """A client for the API at `url`, or for an embedded server if nothing answers there."""
    client = ApiClient(url)
    if client.healthy():
        return client
    return ApiClient(_start_embedded())
