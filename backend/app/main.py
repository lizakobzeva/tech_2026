from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database import engine
from app.models import Base
from app.router import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="DatingBot Backend",
    description="FastAPI backend for the Telegram Dating Bot",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(router)


@app.get("/health")
async def health_check():
    return {"status": "ok"}
