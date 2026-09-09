from fastapi import FastAPI

app = FastAPI(title="Home.Media Core API")

@app.get("/health")
def healthcheck():
    return {"status": "ok"}
