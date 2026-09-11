import sys
import os
import json
import asyncio
import httpx
from typing import Dict, Any

# Add sdk to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sdk')))
from plugin_sdk import PluginApp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from fastapi import Request

app = PluginApp("telegram_bot")

ptb_app = None

# Await text state: map from user_id -> dict with pending callback metadata
_pending_text_input = {}

@app.get("/health")
def healthcheck():
    bot_token = app.config.get("BOT_TOKEN")
    bot_running = ptb_app is not None

    if not bot_token or not bot_running:
        from fastapi import Response
        return Response(
            content=json.dumps({"status": "degraded", "bot_running": False, "error": "BOT_TOKEN missing"}),
            status_code=503,
            media_type="application/json"
        )
    return {"status": "ok", "bot_running": True}

def get_allowed_users() -> list[int]:
    allowed_json = app.config.get("ALLOWED_USERS", "[]")
    try:
        return json.loads(allowed_json)
    except:
        return []

def is_authorized(user_id: int) -> bool:
    allowed = get_allowed_users()
    return not allowed or user_id in allowed

async def _fetch_catalog():
    catalog = []
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{app.core_internal_url}/api/internal/plugins", timeout=5.0)
            if resp.status_code == 200:
                for p in resp.json():
                    manifest = p.get("manifest", {})
                    if "bot_menu" in manifest:
                        menu_def = manifest["bot_menu"]
                        # Store url to route requests to that plugin later
                        catalog.append({
                            "id": p["plugin_id"],
                            "name": p["name"],
                            "url": p["url"],
                            "title": menu_def.get("title", p["name"]),
                            "icon": menu_def.get("icon", "📦"),
                            "order": menu_def.get("order", 99)
                        })
        except Exception as e:
            print(f"Failed to fetch catalog: {e}")
    catalog.sort(key=lambda x: x["order"])
    return catalog

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        await update.message.reply_text("Unauthorized.")
        return

    # Clear pending text if any
    _pending_text_input.pop(user_id, None)

    catalog = await _fetch_catalog()
    keyboard = []
    for p in catalog:
        keyboard.append([InlineKeyboardButton(f"{p['icon']} {p['title']}", callback_data=f"route:{p['name']}:/")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    await update.message.reply_text(
        "Welcome to Home.Media Hub!\nChoose an app:",
        reply_markup=reply_markup
    )

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    data = query.data
    if not data.startswith("route:"):
        return

    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    plugin_name = parts[1]
    action = parts[2]

    # Resolve URL
    target_plugin = await app.resolve_plugin(plugin_name)
    if not target_plugin or not target_plugin.get("url"):
        await query.edit_message_text(f"Plugin {plugin_name} is offline.")
        return

    url = target_plugin["url"]

    # Send callback to plugin
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{url}/bot/callback",
                json={
                    "user_id": user_id,
                    "username": update.effective_user.username,
                    "action": action
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                await _apply_bot_response(query.message, user_id, plugin_name, resp.json())
            else:
                await query.edit_message_text(f"Plugin error: {resp.status_code}")
        except Exception as e:
            await query.edit_message_text(f"Failed to contact {plugin_name}: {e}")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_authorized(user_id):
        return

    if user_id not in _pending_text_input:
        return

    pending = _pending_text_input.pop(user_id)
    plugin_name = pending["plugin_name"]
    action = pending["action"]
    text_input = update.message.text

    target_plugin = await app.resolve_plugin(plugin_name)
    if not target_plugin or not target_plugin.get("url"):
        await update.message.reply_text(f"Plugin {plugin_name} is offline.")
        return

    url = target_plugin["url"]

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{url}/bot/callback",
                json={
                    "user_id": user_id,
                    "username": update.effective_user.username,
                    "action": action,
                    "text_input": text_input
                },
                timeout=10.0
            )
            if resp.status_code == 200:
                await _apply_bot_response(update.message, user_id, plugin_name, resp.json(), is_new_message=True)
            else:
                await update.message.reply_text(f"Plugin error: {resp.status_code}")
        except Exception as e:
            await update.message.reply_text(f"Failed to contact {plugin_name}: {e}")

async def _apply_bot_response(message_obj, user_id, plugin_name, payload, is_new_message=False):
    text = payload.get("text", "No text provided")
    buttons = payload.get("buttons", [])
    await_text_action = payload.get("await_text")

    keyboard = []
    for row in buttons:
        btn_row = []
        for btn in row:
            btn_row.append(InlineKeyboardButton(btn["text"], callback_data=f"route:{plugin_name}:{btn['action']}"))
        keyboard.append(btn_row)

    # Always append a Back to Hub button if it's a plugin view
    keyboard.append([InlineKeyboardButton("🔙 Back to Hub", callback_data="hub_home")])
    reply_markup = InlineKeyboardMarkup(keyboard)

    if await_text_action:
        _pending_text_input[user_id] = {"plugin_name": plugin_name, "action": await_text_action}

    if payload.get("photo"):
        pass # To be implemented if we want to handle base64 or urls

    if is_new_message:
        await message_obj.reply_text(text, reply_markup=reply_markup)
    else:
        try:
            await message_obj.edit_text(text, reply_markup=reply_markup)
        except:
            pass # Same content error

async def hub_home_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    _pending_text_input.pop(user_id, None)

    catalog = await _fetch_catalog()
    keyboard = []
    for p in catalog:
        keyboard.append([InlineKeyboardButton(f"{p['icon']} {p['title']}", callback_data=f"route:{p['name']}:/")])

    reply_markup = InlineKeyboardMarkup(keyboard) if keyboard else None

    try:
        await query.edit_message_text("Welcome to Home.Media Hub!\nChoose an app:", reply_markup=reply_markup)
    except:
        pass


@app.on_event("startup")
async def start_bot():
    global ptb_app
    bot_token = app.config.get("BOT_TOKEN")
    if not bot_token:
        print("BOT_TOKEN missing. Telegram bot won't start.")
        return

    ptb_app = Application.builder().token(bot_token).build()
    ptb_app.add_handler(CommandHandler("start", start_command))
    ptb_app.add_handler(CallbackQueryHandler(hub_home_callback, pattern="^hub_home$"))
    ptb_app.add_handler(CallbackQueryHandler(handle_callback, pattern="^route:"))
    ptb_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    await ptb_app.initialize()
    await ptb_app.start()
    await ptb_app.updater.start_polling()
    print("Telegram bot polling started")

@app.on_event("shutdown")
async def stop_bot():
    if ptb_app:
        await ptb_app.updater.stop()
        await ptb_app.stop()
        await ptb_app.shutdown()


@app.post("/bot/notify")
async def notify_users(request: Request):
    """
    Endpoint for other plugins to send notifications to users.
    Payload: {"message": "Hello!", "user_ids": [1234, ...]}
    """
    bot_token = app.config.get("BOT_TOKEN")
    if not bot_token:
        return {"error": "BOT_TOKEN not configured"}

    data = await request.json()
    message = data.get("message")
    user_ids = data.get("user_ids", [])

    if not message or not user_ids:
        return {"error": "Invalid payload"}

    async with httpx.AsyncClient() as client:
        for uid in user_ids:
            try:
                await client.post(
                    f"https://api.telegram.org/bot{bot_token}/sendMessage",
                    json={"chat_id": uid, "text": message}
                )
            except Exception as e:
                print(f"Failed to send to {uid}: {e}")

    return {"status": "sent"}

if __name__ == "__main__":
    app.serve()
