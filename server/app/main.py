"""LAN Stream signaling server entry point."""

from aiohttp import web


async def health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "lan-stream-server"})


def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", health)
    return app


if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=8080)
