"""LAN Stream server serving the browser client and WebRTC signaling."""

from __future__ import annotations

from pathlib import Path

from aiohttp import web

from server.signaling.registry import StreamRegistry
from server.signaling.websocket import signaling
from server.streams.api import sources

ROOT = Path(__file__).resolve().parents[2]
CLIENT_DIR = ROOT / "client"


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "lan-stream-server"})


async def index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(CLIENT_DIR / "index.html")


def create_app() -> web.Application:
    app = web.Application()
    app["registry"] = StreamRegistry()
    app.router.add_get("/health", health)
    app.router.add_get("/ws", signaling)
    app.router.add_get("/api/sources", sources)
    app.router.add_get("/", index)
    app.router.add_static("/js", CLIENT_DIR / "js")
    app.router.add_static("/css", CLIENT_DIR / "css")
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)
