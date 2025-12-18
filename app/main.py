from contextlib import asynccontextmanager
from fastapi import FastAPI
from pydantic import BaseModel
from app.core.loader import load_data
from app.api.endpoints import operators

class RootResponse(BaseModel):
    message: str

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API starting up. Performing initial data load...")
    load_data()
    print("Startup data load complete.")
    yield

app = FastAPI(
    title="Arknights Game Data API",
    description="An API to query Arknights operator data from the local game data files.",
    lifespan=lifespan
)

@app.get("/", response_model=RootResponse, operation_id="readRoot")
def read_root():
    return {"message": "欢迎使用明日方舟干员数据查询 API"}

app.include_router(operators.router, prefix="/api")
