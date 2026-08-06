from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.exception_handlers import register_exception_handlers
from app.routers import auth

app = FastAPI(
    title="Devboard Auth Service",
)
register_exception_handlers(app)
app.include_router(auth.router)

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/health/db")
async def health_db(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok, baza de date functioneaza corect"}
    except Exception as e:
        return {"status": "error", "details": str(e)}
    