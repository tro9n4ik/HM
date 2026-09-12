import os
import sys
from pathlib import Path

import httpx
import hashlib
import json
import logging
import re
from typing import Dict, Any, List
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from plugin_sdk import PluginApp
import asyncio
import urllib.parse
from threading import Lock

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("torrents")

app = PluginApp("torrents")

# Simple ephemeral cache for TG Bot state (short_hash -> full metadata)
tg_state_cache = {}
TRACKED_FILE = Path(__file__).parent / "tracked.json"
track_lock = Lock()

def get_short_id(data: str) -> str:
    """Stable 10-char hash for TG bot"""
    return hashlib.sha1(data.encode()).hexdigest()[:10]

# --- QBITTORRENT API ---
async def _qbit_login(client: httpx.AsyncClient) -> bool:
    url = f"{app.config.get('qbit_url').rstrip('/')}/api/v2/auth/login"
    data = {
        "username": app.config.get('qbit_username'),
        "password": app.config.get('qbit_password')
    }
    resp = await client.post(url, data=data)
    if resp.text == "Ok.":
        return True
    return False

async def get_qbit_torrents(client: httpx.AsyncClient, filter_state: str):
    if not await _qbit_login(client):
        raise Exception("qBittorrent login failed")
    url = f"{app.config.get('qbit_url').rstrip('/')}/api/v2/torrents/info"
    resp = await client.get(url, params={"filter": filter_state})
    resp.raise_for_status()
    return resp.json()

async def add_to_qbit(magnet_url: str, category: str = ""):
    async with httpx.AsyncClient(timeout=10.0) as client:
        if not await _qbit_login(client):
            raise Exception("qBittorrent login failed")

        url = f"{app.config.get('qbit_url').rstrip('/')}/api/v2/torrents/add"
        data = {
            "urls": magnet_url,
            "category": category
        }
        resp = await client.post(url, data=data)
        if resp.status_code != 200:
            raise Exception(f"Failed to add torrent: {resp.text}")

# --- PROWLARR API ---
async def search_prowlarr(query: str):
    base = app.config.get("prowlarr_url", "").rstrip("/")
    api_key = app.config.get("prowlarr_api_key")
    if not base or not api_key:
        raise Exception("Prowlarr config missing")

    url = f"{base}/api/v1/search"
    params = {
        "query": query,
        "type": "search",
        "apikey": api_key
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json()

def parse_release_info(title: str):
    quality = "Unknown"
    if re.search(r'2160p|4K|UHD', title, re.IGNORECASE): quality = "4K"
    elif re.search(r'1080p', title, re.IGNORECASE): quality = "1080p"
    elif re.search(r'720p', title, re.IGNORECASE): quality = "720p"

    hdr = "HDR" if re.search(r'HDR|DV|DoVi', title, re.IGNORECASE) else ""

    voice = "Original/Sub"
    if re.search(r'DUB|Дубляж|Дублированный', title, re.IGNORECASE): voice = "Дубляж"
    elif re.search(r'MVO|Многоголосый|PVO|Профессиональный', title, re.IGNORECASE): voice = "Многоголосый"
    elif re.search(r'L1|L2', title, re.IGNORECASE): voice = "Любительский"
    elif re.search(r'Rus|Рус', title, re.IGNORECASE): voice = "Rus"

    return {"quality": quality, "hdr": hdr, "voice": voice}

# --- TMDB API ---
async def search_tmdb(query: str):
    api_key = app.config.get("tmdb_api_key")
    if not api_key:
        raise Exception("TMDb API Key missing")

    url = "https://api.themoviedb.org/3/search/multi"
    params = {
        "api_key": api_key,
        "query": query,
        "language": "ru-RU"
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json().get("results", [])

        # Filter and format
        results = []
        for item in data:
            if item.get("media_type") not in ["movie", "tv"]:
                continue
            title = item.get("title") or item.get("name")
            year_str = item.get("release_date") or item.get("first_air_date") or ""
            year = year_str[:4] if year_str else ""

            poster = None
            if item.get("poster_path"):
                poster = f"https://image.tmdb.org/t/p/w500{item['poster_path']}"

            results.append({
                "id": item["id"],
                "type": item["media_type"],
                "title": title,
                "original_title": item.get("original_title") or item.get("original_name"),
                "year": year,
                "overview": item.get("overview"),
                "poster": poster
            })
        return results


# --- WEB ENDPOINTS ---
@app.get("/api/search")
async def web_search(query: str):
    try:
        results = await search_tmdb(query)
        return {"results": results}
    except Exception as e:
        logger.error(e)
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/api/releases")
async def web_releases(title: str, year: str = ""):
    try:
        query = f"{title} {year}".strip()
        data = await search_prowlarr(query)

        processed = []
        for item in data:
            info = parse_release_info(item.get("title", ""))
            processed.append({
                "title": item.get("title"),
                "size": item.get("size", 0),
                "seeders": item.get("seeders", 0),
                "peers": item.get("leechers", 0),
                "indexer": item.get("indexer"),
                "magnetUrl": item.get("magnetUrl") or item.get("downloadUrl"),
                "info": info
            })

        # Sort by seeders
        processed.sort(key=lambda x: x["seeders"], reverse=True)
        return {"releases": processed}
    except Exception as e:
        logger.error(e)
        return JSONResponse(status_code=500, content={"detail": str(e)})

@app.get("/api/categories")
async def get_categories():
    cat = app.config.get("categories", [])
    if isinstance(cat, str):
        try: cat = json.loads(cat)
        except: cat = ["movies", "tv"]
    return {"categories": cat}

@app.post("/api/download")
async def web_download(req: Request):
    try:
        data = await req.json()
        await add_to_qbit(data["url"], data.get("category", ""))
        return {"status": "ok"}
    except Exception as e:
        logger.error(e)
        return JSONResponse(status_code=500, content={"detail": str(e)})

# --- TRACKING ---
@app.get("/api/tracked")
async def get_tracked():
    with track_lock:
        if TRACKED_FILE.exists():
            with open(TRACKED_FILE, "r") as f:
                return json.load(f)
        return []

@app.post("/api/tracked")
async def add_tracked(req: Request):
    data = await req.json()
    with track_lock:
        current = []
        if TRACKED_FILE.exists():
            with open(TRACKED_FILE, "r") as f:
                current = json.load(f)
        if not any(x["tmdb_id"] == data.get("tmdb_id") for x in current):
            current.append(data)
            with open(TRACKED_FILE, "w") as f:
                json.dump(current, f)
    return {"status": "ok"}

@app.delete("/api/tracked/{id}")
async def del_tracked(id: int):
    with track_lock:
        if TRACKED_FILE.exists():
            with open(TRACKED_FILE, "r") as f:
                current = json.load(f)
            current = [x for x in current if x["tmdb_id"] != id]
            with open(TRACKED_FILE, "w") as f:
                json.dump(current, f)
    return {"status": "ok"}

@app.get("/api/downloads")
async def web_downloads():
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            dl = await get_qbit_torrents(client, "downloading")
            seed = await get_qbit_torrents(client, "seeding")
            return {"downloading": dl, "seeding": seed}
    except Exception as e:
        return JSONResponse(status_code=500, content={"detail": str(e)})


# --- TELEGRAM BOT HUB ---
async def bot_menu():
    return {
        "text": "🎬 Торренты",
        "buttons": [
            [{"text": "🔍 Поиск фильма/сериала", "action": "t_search_init"}]
        ]
    }

@app.post("/bot/callback")
async def bot_callback(req: Request):
    data = await req.json()
    cb = data.get("action", "")
    text = data.get("text_input", "")

    if cb == "t_search_init":
        return {
            "text": "Отправьте название фильма или сериала в чат:",
            "await_text": "t_search_exec",
            "buttons": [[{"text": "Отмена", "action": "t_menu"}]]
        }

    elif cb == "t_search_exec" or text:
        query = text
        if not query:
            return {"text": "Пустой запрос", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

        try:
            results = await search_tmdb(query)
            if not results:
                return {"text": "Ничего не найдено", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

            buttons = []
            for r in results[:5]: # Top 5
                title = f"{r['title']} ({r['year']})"
                slug = f"{r['title']} {r['year']}"
                hash_id = get_short_id(slug)
                tg_state_cache[hash_id] = slug
                buttons.append([{
                    "text": title,
                    "action": f"t_rels_{hash_id}"
                }])
            buttons.append([{"text": "🔙 В главное меню", "action": "t_menu"}])
            return {"text": f"Результаты по: {query}", "buttons": buttons}
        except Exception as e:
            return {"text": f"Ошибка: {e}", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

    elif cb.startswith("t_rels_"):
        hash_id = cb[7:]
        slug = tg_state_cache.get(hash_id)
        if not slug:
            return {"text": "Сессия устарела", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

        try:
            releases = await search_prowlarr(slug)

            # Filter and sort
            processed = []
            for item in releases:
                if not item.get("magnetUrl") and not item.get("downloadUrl"): continue
                processed.append({
                    "title": item.get("title")[:30] + "..",
                    "size_gb": round(item.get("size", 0) / (1024**3), 2),
                    "seeders": item.get("seeders", 0),
                    "url": item.get("magnetUrl") or item.get("downloadUrl")
                })

            processed.sort(key=lambda x: x["seeders"], reverse=True)

            if not processed:
                return {"text": "Нет раздач на трекерах", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

            buttons = []
            for r in processed[:4]:
                r_hash = get_short_id(r["url"])
                tg_state_cache[r_hash] = r["url"]

                txt = f"S:{r['seeders']} | {r['size_gb']}GB | {r['title']}"
                buttons.append([{
                    "text": txt,
                    "action": f"t_dl_{r_hash}"
                }])
            buttons.append([{"text": "🔙 Назад", "action": "t_menu"}])
            return {"text": f"Раздачи: {slug}", "buttons": buttons}
        except Exception as e:
            return {"text": f"Ошибка: {e}", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

    elif cb.startswith("t_dl_"):
        hash_id = cb[5:]
        url = tg_state_cache.get(hash_id)
        if not url:
            return {"text": "Ошибка ссылки", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

        try:
            await add_to_qbit(url, "")
            return {"text": "✅ Торрент добавлен в qBittorrent", "buttons": [[{"text": "Главное меню", "action": "t_menu"}]]}
        except Exception as e:
            return {"text": f"Ошибка: {e}", "buttons": [[{"text": "Назад", "action": "t_menu"}]]}

    elif cb == "t_menu" or cb == "/":
        return await bot_menu()

    return await bot_menu()


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
    app.serve()
