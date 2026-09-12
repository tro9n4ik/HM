import os
from plugin_sdk import PluginApp

app = PluginApp("example_plugin")

@app.get("/")
def read_root():
    debug = app.config.get("DEBUG_MODE", "False")
    return {"message": "Hello from Example Plugin", "debug": debug}

if __name__ == "__main__":
    app.serve()
