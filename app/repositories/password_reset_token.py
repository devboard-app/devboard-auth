from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import UnexpectedException
from app.models.user import PasswordResetToken, User


async def insert_password_reset_token(user: User, token_hash: str, db: AsyncSession) -> None:
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE_MINUTES)
        password_reset_token = PasswordResetToken(user_id=user.id, token_hash=token_hash, expires_at=expires_at)
        db.add(password_reset_token)
        await db.flush()
    except Exception:
        await db.rollback()
        raise UnexpectedException()

async def get_password_reset_token_by_hash(token_hash: str, db: AsyncSession) -> PasswordResetToken | None:
    result = await db.execute(select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash))
    return result.scalar_one_or_none()

async def mark_password_reset_token_used(password_reset_token: PasswordResetToken, db: AsyncSession) -> None:
    password_reset_token.used = True
    await db.flush()