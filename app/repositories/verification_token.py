from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.exceptions import UnexpectedException
from sqlalchemy.ext.asyncio import AsyncSession
from models.user import User, VerificationToken
from app.config import settings

async def insert_verification_token(user: User, token_hash: str, db: AsyncSession)-> None:
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(days= settings.VERIFICATION_TOKEN_EXPIRE_DAYS)
        verification_token = VerificationToken(user_id= user.id, token_hash=token_hash, expires_at=expires_at)
        db.add(verification_token)
        await db.flush()
    except Exception:
        await db.rollback()
        raise UnexpectedException()

async def get_verification_token_by_hash(token_hash: str, db: AsyncSession) -> VerificationToken | None:
    result = await db.execute(select(VerificationToken).where(VerificationToken.token_hash == token_hash))
    return result.scalar_one_or_none()
