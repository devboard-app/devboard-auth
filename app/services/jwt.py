import uuid
import secrets
import hashlib
from fastapi import HTTPException, status
from datetime import datetime, timedelta, timezone
from app.config import settings
from jose import jwt, JWTError
from app.models.user import RefreshToken
from sqlalchemy import select

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload ={
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    }
    return jwt.encode(payload, settings.JWT_SECRET, settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict:
    try: 
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        raise ValueError("Invalid or expired token")
    

def generate_refresh_token() -> tuple[str, str]:
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash

async def create_refresh_token(user_id: uuid.UUID, db, commit=True) ->str | None:
    try:
        raw_token, token_hash = generate_refresh_token()

        refresh_token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        )
        db.add(refresh_token)
        if commit:
            await db.commit()
        return raw_token
    except Exception:
        if commit:
            await db.rollback()
        return None


async def search_refresh_token_in_db(token: str, db) -> RefreshToken | None:
    hashed_refresh_token = hashlib.sha256(token.encode()).hexdigest()
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash == hashed_refresh_token))
    refresh_token_found = result.scalar_one_or_none()
    if refresh_token_found is None:
        return None
    if refresh_token_found.revoked :
        return None
    if refresh_token_found.expires_at < datetime.now(timezone.utc):
        return None
    return refresh_token_found

    


