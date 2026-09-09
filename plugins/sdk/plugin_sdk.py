import os
import urllib.request
import urllib.error
import json
from typing import Dict, Any, Callable

class PluginSDK:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.core_url = os.environ.get("CORE_INTERNAL_URL", "http://127.0.0.1:8142")
        self.port = int(os.environ.get("PLUGIN_PORT", "8100"))
        self.plugin_id = os.environ.get("PLUGIN_ID", self.plugin_name)

    def register(self):
        print(f"Registering plugin {self.plugin_name} with core at {self.core_url}...")
        try:
            req = urllib.request.Request(
                f"{self.core_url}/api/internal/register",
                data=json.dumps({"name": self.plugin_name, "port": self.port}).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                pass
        except Exception as e:
            print(f"Failed to register with core: {e}")

    def get_config(self, key: str) -> str:
        print(f"Fetching config {key} from core...")
        try:
            req = urllib.request.Request(f"{self.core_url}/api/internal/plugins/{self.plugin_id}/config")
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode('utf-8'))
                return data.get(key, "")
        except Exception as e:
            print(f"Failed to fetch config from core: {e}")
            return ""

    def serve(self, app_handler: Callable):
        import uvicorn
        print(f"Starting {self.plugin_name} on port {self.port}...")
        uvicorn.run(app_handler, host="127.0.0.1", port=self.port)

sdk = PluginSDK
