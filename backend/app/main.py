from fastapi import FastAPI
from app.api.main import api_router

app = FastAPI(title="Bossy Radar API")

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"Hello": "World"}
