
import os
from plugin_sdk import PluginApp
app = PluginApp("dummy_plugin")
@app.get("/health")
def health(): return {"status": "ok"}
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=int(os.environ.get("PLUGIN_PORT", 8999)))
