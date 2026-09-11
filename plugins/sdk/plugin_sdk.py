import os
import httpx
from fastapi import FastAPI
import asyncio
from typing import Dict, Any

class Config:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default=None):
        return self._data.get(key, default)

    def to_dict(self):
        return self._data

class PluginApp(FastAPI):
    def __init__(self, name: str, *args, **kwargs):
        super().__init__(title=name, *args, **kwargs)
        self.plugin_name = name
        self.core_internal_url = os.environ.get("CORE_INTERNAL_URL", "http://127.0.0.1:8142")
        self.port = int(os.environ.get("PLUGIN_PORT", "8100"))
        self.plugin_id = os.environ.get("PLUGIN_ID", self.plugin_name)
        self.config = Config({})

        @self.get("/health")
        def healthcheck():
            return {"status": "ok"}

        @self.on_event("startup")
        async def on_startup():
            await self._load_config()
            await self._register_with_core()

    async def _register_with_core(self):
        print(f"Registering plugin {self.plugin_name} with core at {self.core_internal_url}...")
        async with httpx.AsyncClient() as client:
            try:
                await client.post(
                    f"{self.core_internal_url}/api/internal/register",
                    json={"name": self.plugin_name, "port": self.port},
                    timeout=5.0
                )
            except Exception as e:
                print(f"Failed to register with core: {e}")

    async def _load_config(self):
        print("Fetching config from core...")
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(
                    f"{self.core_internal_url}/api/internal/plugins/{self.plugin_id}/config",
                    timeout=5.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    if asyncio.iscoroutine(data):
                        data = await data
                    self.config = Config(data)
            except Exception as e:
                print(f"Failed to fetch config from core: {e}")

    async def resolve_plugin(self, target_plugin_name: str) -> dict | None:
        async with httpx.AsyncClient() as client:
            try:
                resp = await client.get(f"{self.core_internal_url}/api/internal/plugins", timeout=5.0)
                if resp.status_code == 200:
                    plugins = resp.json()
                    if asyncio.iscoroutine(plugins):
                        plugins = await plugins
                    for p in plugins:
                        if p.get("name") == target_plugin_name:
                            return p
            except Exception as e:
                print(f"Failed to resolve plugin {target_plugin_name}: {e}")
        return None

    def serve(self):
        import uvicorn
        print(f"Starting {self.plugin_name} on port {self.port}...")
        uvicorn.run(self, host="127.0.0.1", port=self.port)
