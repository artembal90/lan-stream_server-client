"""WebSocket signaling foundation.

The message routing is intentionally minimal at this stage. WebRTC SDP and
ICE exchange will be added in the next implementation step.
"""

from aiohttp import WSMsgType, web


async def signaling(request: web.Request) -> web.WebSocketResponse:
    ws = web.WebSocketResponse(heartbeat=30)
    await ws.prepare(request)

    async for message in ws:
        if message.type == WSMsgType.TEXT:
            await ws.send_json({"type": "ack", "message": "signaling channel ready"})
        elif message.type == WSMsgType.ERROR:
            break

    return ws
