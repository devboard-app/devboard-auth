
import uuid

from fastapi import HTTPException
from sqlalchemy import  select, text
from app.models.user import User
from sqlalchemy.exc import IntegrityError
from enum import Enum
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.jwt import search_refresh_token_in_db


class CreateUserError(Enum):
    CONFLICT = "conflict"
    UNEXPECTED = "unexpected"

async def check_email_exists(email: str, db) -> bool:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar() is not None

async def create_user(user_email: str, user_hashed_password: str, db) -> tuple[User | None, CreateUserError | None]:
    try:
        new_user = User(email=user_email, hashed_password=user_hashed_password,
                         is_verified=True)  # temporary - remove this line when email verification is implemented
        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)
        return new_user, None
    except IntegrityError:
        await db.rollback()
        return None, CreateUserError.CONFLICT
    except Exception:
        await db.rollback()
        return None, CreateUserError.UNEXPECTED

async def get_user_by_email(email: str, db) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none() 

async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession):
    result = await db.execute(select(User).where(User.id==user_id))
    return result.scalar_one_or_none()

async def logout_user(token: str, db: AsyncSession)->None:
    refresh_token = await search_refresh_token_in_db(token, db)
    if refresh_token is None:
        return 
    refresh_token.revoked= True
    await db.commit()