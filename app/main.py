from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exception_handlers import register_exception_handlers
from app.infrastructure.http_client import close_http_client, open_http_client
from app.infrastructure.redis_client import close_redis_client, open_redis_client
from app.routers import auth, internal


@asynccontextmanager
async def lifespan(app: FastAPI):
    await open_http_client()
    await open_redis_client()
    yield
    await close_http_client()
    await close_redis_client()

app = FastAPI(
    title="Devboard Auth Service",
    lifespan=lifespan
)
register_exception_handlers(app)
app.include_router(auth.router)
app.include_router(internal.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return JSONResponse(status_code=200, content={"status":"ok"})
    except Exception:
        return JSONResponse(status_code=500, content={"status":"error", "details":"db unavailable"})
    