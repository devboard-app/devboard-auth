import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import UnexpectedException
from app.models.user import User, VerificationToken


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

async def get_active_verification_token_by_user_id(user_id: uuid.UUID, db: AsyncSession)-> VerificationToken | None:
    result = await db.execute(select(VerificationToken).where(VerificationToken.user_id==user_id).where(VerificationToken.used==False).where(VerificationToken.expires_at > datetime.now(timezone.utc)).limit(1))
    return result.scalar_one_or_none()

async def mark_verification_token_used(verification_token: VerificationToken, db: AsyncSession)-> None:
    verification_token.used = True
    await db.flush()

async def invalidate_user_verification_tokens(user_id: uuid.UUID, db: AsyncSession) ->None:
    try:
        await db.execute(update(VerificationToken).where(VerificationToken.user_id == user_id).where(VerificationToken.used == False).values(used=True))
    except Exception:
        await db.rollback()
        raise UnexpectedException()