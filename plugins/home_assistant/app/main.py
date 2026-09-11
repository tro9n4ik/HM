import os
import sys
from pathlib import Path

# Fix python path for local execution during dev
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import httpx
import hashlib
import json
import logging
from threading import Lock
from typing import Dict, Any, List
from fastapi import Request
from fastapi.responses import JSONResponse, FileResponse
from plugins.sdk.plugin_sdk import PluginApp

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("home_assistant")

app = PluginApp()

# Internal State
class HAState:
    def __init__(self):
        self.lock = Lock()
        self.entities = []
        self.hash_map = {} # short_hash -> full_entity_id
        self._busy = False
        self.last_error = None

state = HAState()

def _get_short_hash(entity_id: str) -> str:
    """Generate a stable 10-char hash to comply with Telegram callback limits"""
    return hashlib.sha1(entity_id.encode()).hexdigest()[:10]

async def _call_ha_api(client: httpx.AsyncClient, method: str, path: str, json_data: dict = None) -> Any:
    url = f"{app.config.get('ha_url').rstrip('/')}/api{path}"
    headers = {
        "Authorization": f"Bearer {app.config.get('ha_token')}",
        "Content-Type": "application/json"
    }
    logger.debug(f"Calling HA API: {method} {url}")
    resp = await client.request(method, url, headers=headers, json=json_data, timeout=10.0)
    resp.raise_for_status()
    return resp.json()

async def refresh_entities():
    with state.lock:
        if state._busy:
            return
        state._busy = True

    try:
        if not app.config.get("ha_token"):
            raise ValueError("HA Token is missing")

        async with httpx.AsyncClient() as client:
            data = await _call_ha_api(client, "GET", "/states")

        hide_list = app.config.get("hide", [])
        if isinstance(hide_list, str):
            try: hide_list = json.loads(hide_list)
            except: hide_list = []

        filtered = []
        new_hash_map = {}
        for ent in data:
            if ent["entity_id"] in hide_list:
                continue
            filtered.append(ent)
            new_hash_map[_get_short_hash(ent["entity_id"])] = ent["entity_id"]

        with state.lock:
            state.entities = filtered
            state.hash_map = new_hash_map
            state.last_error = None

        app.ready = True
        app.ready_detail = "Connected"
    except Exception as e:
        logger.error(f"Failed to refresh HA entities: {e}")
        with state.lock:
            state.last_error = str(e)
        app.ready = False
        app.ready_detail = f"HA Error: {e}"
    finally:
        with state.lock:
            state._busy = False

# Register a periodic background task to poll HA states
@app.periodic(interval_seconds=app.config.get("poll_seconds", 30))
async def poll_ha():
    await refresh_entities()

@app.get("/status")
async def get_status():
    with state.lock:
        return {
            "ready": app.ready,
            "detail": app.ready_detail,
            "entities_count": len(state.entities),
            "last_error": state.last_error
        }

@app.get("/api/entities")
async def get_entities():
    with state.lock:
        return state.entities

@app.post("/api/refresh")
async def force_refresh():
    await refresh_entities()
    return {"status": "ok"}

@app.post("/api/control")
async def control_entity(req: Request):
    try:
        data = await req.json()
        entity_id = data.get("entity_id")
        domain = entity_id.split(".")[0]
        service = data.get("service")
        service_data = data.get("service_data", {})
        service_data["entity_id"] = entity_id

        async with httpx.AsyncClient() as client:
            await _call_ha_api(client, "POST", f"/services/{domain}/{service}", service_data)

        # Async refresh to get immediate state updates
        await refresh_entities()
        return {"status": "ok"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})

# --- TELEGRAM BOT HUB INTEGRATION ---

def build_tg_groups() -> Dict[str, List[str]]:
    raw_groups = app.config.get("tg_groups", {})
    if isinstance(raw_groups, str):
        try: raw_groups = json.loads(raw_groups)
        except: raw_groups = {}

    # Generate auto groups based on domains
    domains = {}
    with state.lock:
        for ent in state.entities:
            domain = ent["entity_id"].split(".")[0]
            if domain not in domains:
                domains[domain] = []
            domains[domain].append(ent["entity_id"])

    # Combine
    final_groups = {}
    for dom, ents in domains.items():
        if len(ents) > 0:
            final_groups[dom.capitalize()] = ents

    # Apply custom groups if defined (overrides)
    if isinstance(raw_groups, dict) and raw_groups:
        for k, v in raw_groups.items():
            if isinstance(v, list):
                final_groups[k] = v

    return final_groups

@app.get("/bot_menu")
async def get_bot_menu():
    groups = build_tg_groups()
    if not groups:
        return {"title": "Home Assistant", "items": [{"text": "Нет устройств", "callback_data": "ha_none"}]}

    items = []
    for group_name in groups.keys():
        # Level 0 callback: root_HA_grp_<group_name_hash> (using a short slug to avoid 64b limit)
        g_hash = hashlib.sha1(group_name.encode()).hexdigest()[:6]
        items.append({
            "text": f"📁 {group_name}",
            "callback_data": f"ha_g_{g_hash}"
        })

    return {
        "title": "Home Assistant",
        "items": items
    }

@app.post("/bot/callback")
async def bot_callback(req: Request):
    """
    Handles callbacks starting with 'ha_'
    Levels:
    ha_g_<hash> -> list entities in group
    ha_e_<short_id> -> view entity controls
    ha_c_<short_id>_<action> -> execute control action
    ha_b -> back to root
    """
    data = await req.json()
    cb = data.get("callback_data", "")

    if cb == "ha_b":
        return await get_bot_menu()

    # Lookup entity from short hash
    def _get_entity(short_id):
        with state.lock:
            eid = state.hash_map.get(short_id)
            if not eid: return None
            return next((e for e in state.entities if e["entity_id"] == eid), None)

    if cb.startswith("ha_g_"):
        g_hash = cb[5:]
        groups = build_tg_groups()
        # Find group by hash
        group_name = next((k for k in groups.keys() if hashlib.sha1(k.encode()).hexdigest()[:6] == g_hash), None)

        if not group_name:
            return {"title": "Группа не найдена", "items": [{"text": "Назад", "callback_data": "ha_b"}]}

        items = []
        for eid in groups[group_name]:
            short_id = _get_short_hash(eid)
            ent = _get_entity(short_id)
            if not ent: continue

            icon = "⚪"
            if ent["state"] in ["on", "playing", "open", "unlocked"]: icon = "🟢"
            elif ent["state"] in ["off", "paused", "closed", "locked"]: icon = "🔴"

            name = ent.get("attributes", {}).get("friendly_name", eid)
            items.append({
                "text": f"{icon} {name}",
                "callback_data": f"ha_e_{short_id}"
            })

        items.append({"text": "🔙 Назад", "callback_data": "ha_b"})
        return {"title": f"HA: {group_name}", "items": items}

    elif cb.startswith("ha_e_"):
        short_id = cb[5:]
        ent = _get_entity(short_id)

        if not ent:
            return {"title": "Устройство не найдено", "items": [{"text": "Назад", "callback_data": "ha_b"}]}

        name = ent.get("attributes", {}).get("friendly_name", ent["entity_id"])
        domain = ent["entity_id"].split(".")[0]
        status_text = f"{name}\nСтатус: {ent['state']}"

        items = []
        if domain in ["light", "switch", "input_boolean"]:
            items.append({"text": "Toggle", "callback_data": f"ha_c_{short_id}_toggle"})
        elif domain == "cover":
            items.extend([
                {"text": "Open", "callback_data": f"ha_c_{short_id}_open_cover"},
                {"text": "Close", "callback_data": f"ha_c_{short_id}_close_cover"}
            ])
        elif domain == "media_player":
            items.extend([
                {"text": "Play/Pause", "callback_data": f"ha_c_{short_id}_media_play_pause"},
            ])

        # Optional attr info
        if "brightness" in ent.get("attributes", {}):
            status_text += f"\nЯркость: {ent['attributes']['brightness']}"

        items.append({"text": "🔙 К списку", "callback_data": "ha_b"}) # simplification: back to root
        return {"title": status_text, "items": items}

    elif cb.startswith("ha_c_"):
        # Format: ha_c_<short_id>_<service>
        parts = cb.split("_", 3)
        if len(parts) >= 4:
            short_id = parts[2]
            service = parts[3]
            ent = _get_entity(short_id)
            if ent:
                domain = ent["entity_id"].split(".")[0]
                try:
                    async with httpx.AsyncClient() as client:
                        await _call_ha_api(client, "POST", f"/services/{domain}/{service}", {"entity_id": ent["entity_id"]})
                    # trigger background refresh
                    import asyncio
                    asyncio.create_task(refresh_entities())
                except Exception as e:
                    logger.error(f"HA control error via bot: {e}")

            # Return to entity view
            return await bot_callback(Request(scope={"type": "http"}, receive=None)) # We mock request mostly, but better just return struct.

        return {"title": "Error", "items": [{"text": "Back", "callback_data": "ha_b"}]}

    return {"title": "Unknown action", "items": [{"text": "Back", "callback_data": "ha_b"}]}


# --- WEB SPA ROUTE ---
@app.get("/")
@app.get("/{path:path}")
async def serve_spa(path: str = ""):
    web_dir = Path(__file__).parent / "web"
    file_path = web_dir / path
    if file_path.exists() and file_path.is_file():
        return FileResponse(file_path)
    return FileResponse(web_dir / "index.html")

if __name__ == "__main__":
    import uvicorn
    # Test local execution
    port = int(os.environ.get("PLUGIN_PORT", 8124))
    uvicorn.run(app, host="0.0.0.1", port=port)
