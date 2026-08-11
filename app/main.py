from fastapi import Depends, FastAPI
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exception_handlers import register_exception_handlers
from app.routers import auth, internal

app = FastAPI(
    title="Devboard Auth Service",
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
    