import os
import requests
import time
from typing import Dict, Any, Callable

class PluginSDK:
    def __init__(self, plugin_name: str):
        self.plugin_name = plugin_name
        self.core_url = os.environ.get("CORE_INTERNAL_URL", "http://127.0.0.1:8142")
        self.port = int(os.environ.get("PLUGIN_PORT", "8100"))

    def register(self):
        print(f"Registering plugin {self.plugin_name}...")
        # Simulate registration logic with the core

    def serve(self, app_handler: Callable):
        import uvicorn
        print(f"Starting {self.plugin_name} on port {self.port}...")
        uvicorn.run(app_handler, host="127.0.0.1", port=self.port)

sdk = PluginSDK
