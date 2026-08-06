import secrets
import hashlib
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta, timezone
from app.config import settings
from jose import jwt, JWTError
from app.models.user import RefreshToken
from app.repositories.token import get_refresh_token_by_hash
from app.exceptions import InvalidTokenException, TokenExpiredException

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


async def validate_refresh_token(token: str, db: AsyncSession) -> RefreshToken:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    refresh_token = await get_refresh_token_by_hash(token_hash, db)
    if refresh_token is None or refresh_token.revoked:
        raise InvalidTokenException()
    if refresh_token.expires_at < datetime.now(timezone.utc):
        raise TokenExpiredException()
    return refresh_token



    


