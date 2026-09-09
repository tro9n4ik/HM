from fastapi import FastAPI
import sys
import os

# Add sdk to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'sdk')))
from plugin_sdk import sdk

plugin = sdk("example_plugin")
app = FastAPI(title="Example Plugin")

@app.get("/health")
def healthcheck():
    return {"status": "ok"}

@app.get("/")
def read_root():
    # Example using get_config
    debug = plugin.get_config("DEBUG_MODE")
    return {"message": "Hello from Example Plugin", "debug": debug}

if __name__ == "__main__":
    plugin.register()
    plugin.serve(app)
