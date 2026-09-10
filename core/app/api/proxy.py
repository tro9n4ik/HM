from fastapi import APIRouter, Request, HTTPException, Depends, WebSocket, Query
from fastapi.responses import StreamingResponse
import httpx
import websockets
from websockets.exceptions import ConnectionClosed
from app.database import get_db
from sqlalchemy.orm import Session
from app.models.plugin import Plugin
from app.api.deps import get_current_user_from_token, get_current_user

router = APIRouter(tags=["proxy"])

client = httpx.AsyncClient()

@router.websocket("/plugins/{plugin_name}/{path:path}")
async def proxy_websocket(plugin_name: str, path: str, websocket: WebSocket, db: Session = Depends(get_db)):
    token = websocket.cookies.get("access_token")
    if not token:
        await websocket.close(code=1008, reason="Missing token")
        return

    try:
        user = get_current_user_from_token(token, db)
    except Exception:
        await websocket.close(code=1008, reason="Invalid token")
        return

    plugin = db.query(Plugin).filter(Plugin.name == plugin_name).first()
    if not plugin or (plugin.status != "running" and plugin.status != "degraded"):
        await websocket.close(code=1011, reason="Plugin not available")
        return

    await websocket.accept()

    query = websocket.url.query
    ws_url = f"ws://127.0.0.1:{plugin.port}/{path}"
    if query:
        ws_url += f"?{query}"

    try:
        async with websockets.connect(ws_url) as target_ws:
            import asyncio

            async def forward_to_target():
                try:
                    while True:
                        data = await websocket.receive()
                        if "text" in data:
                            await target_ws.send(data["text"])
                        elif "bytes" in data:
                            await target_ws.send(data["bytes"])
                        elif data["type"] == "websocket.disconnect":
                            break
                except Exception:
                    pass

            async def forward_to_client():
                try:
                    while True:
                        message = await target_ws.recv()
                        if isinstance(message, str):
                            await websocket.send_text(message)
                        else:
                            await websocket.send_bytes(message)
                except Exception:
                    pass

            await asyncio.gather(forward_to_target(), forward_to_client())
    except Exception:
        pass
    finally:
        try:
            await websocket.close()
        except:
            pass

@router.api_route("/plugins/{plugin_name}/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def proxy_to_plugin(plugin_name: str, path: str, request: Request, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    plugin = db.query(Plugin).filter(Plugin.name == plugin_name).first()
    if not plugin:
        raise HTTPException(status_code=404, detail="Plugin not found")

    if plugin.status != "running" and plugin.status != "degraded":
        raise HTTPException(status_code=502, detail=f"Plugin is {plugin.status}")

    url = httpx.URL(path=path, query=request.url.query.encode("utf-8"))

    headers = dict(request.headers)
    headers.pop("host", None)

    try:
        req = client.build_request(
            request.method,
            f"http://127.0.0.1:{plugin.port}/{url}",
            headers=headers,
            content=request.stream()
        )

        resp = await client.send(req, stream=True)

        return StreamingResponse(
            resp.aiter_raw(),
            status_code=resp.status_code,
            headers=dict(resp.headers),
            background=resp.aclose
        )
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")
