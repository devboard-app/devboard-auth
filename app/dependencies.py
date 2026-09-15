import hmac

from fastapi import Header, HTTPException
from fastapi.security import HTTPBearer

from app.config import settings

oauth2_scheme = HTTPBearer()

async def verify_internal_key(x_service_key: str = Header(...)):
    if not hmac.compare_digest(x_service_key, settings.INTERNAL_API_KEY):
        raise HTTPException(status_code=403, detail="Forbidden")