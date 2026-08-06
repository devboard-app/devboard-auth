import uuid
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import UnexpectedException
from app.models.user import RefreshToken


async def get_refresh_token_by_hash(hash_token: str, db: AsyncSession)-> RefreshToken | None:
    result = await db.execute(select(RefreshToken).where(RefreshToken.token_hash==hash_token))
    return result.scalar_one_or_none()

async def revoke_and_insert_new_refresh_token(old_token: RefreshToken,  user_id: uuid.UUID, token_hash: str, expires_at: datetime, db )-> None:
    await revoke_refresh_token(old_token, db)
    await insert_new_refresh_token(user_id, token_hash, expires_at, db)

async def revoke_refresh_token(refresh_token: RefreshToken, db: AsyncSession)-> None:
    try:
        refresh_token.revoked = True
        await db.flush()
    except Exception:
        await db.rollback()
        raise UnexpectedException()

async def insert_new_refresh_token(user_id: uuid.UUID, token_hash: str, expires_at: datetime, db: AsyncSession ) -> None:
    try:
        token = RefreshToken(user_id=user_id, token_hash=token_hash, expires_at=expires_at)
        db.add(token)
        await db.flush()
    except Exception:
        await db.rollback()
        raise UnexpectedException()

async def delete_all_user_tokens(user_id: uuid.UUID, db: AsyncSession) -> None:
    try:
        await db.execute(update(RefreshToken).where(RefreshToken.user_id==user_id).values(revoked=True))
        await db.flush()
    except Exception:
        await db.rollback()
        raise UnexpectedException()

