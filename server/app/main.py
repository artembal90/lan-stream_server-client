"""LAN Stream signaling server entry point."""

from aiohttp import web

from server.signaling.websocket import signaling
from server.streams.api import sources


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "lan-stream-server"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    app.router.add_get("/ws", signaling)
    app.router.add_get("/api/sources", sources)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)
