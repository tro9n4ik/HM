import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../plugins/sdk')))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from plugins.telegram_bot.main import app

# For starlette TestClient with older httpx, we have to bypass httpx conflict sometimes, but we downgraded httpx back so TestClient(app) works.

client = TestClient(app)

# Trigger startup events to run start_bot (which should set ready=False because no BOT_TOKEN)
with client:
    response = client.get("/health")
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.json()}")
