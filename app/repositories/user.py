import uuid

from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.exceptions import EmailAlreadyExistsException, UnexpectedException
from app.models.user import User


async def insert_user(user_email: str, user_hashed_password: str, db: AsyncSession)-> User:
    try:
        user = User(email=user_email, hashed_password=user_hashed_password)
        db.add(user)
        await db.flush()
        await db.refresh(user)
        return user
    except IntegrityError:
        await db.rollback()
        raise EmailAlreadyExistsException()
    except Exception:
        await db.rollback()
        raise UnexpectedException()


async def get_user_by_email(email:str, db: AsyncSession)->User | None:
    result = await db.execute(select(User).where(User.email==email))
    return result.scalar_one_or_none()

async def check_email_exists(email:str, db: AsyncSession)->bool:
    result = await db.execute(select(User.id).where(User.email==email))
    return result.scalar_one_or_none() is not None

async def get_user_by_id(user_id: uuid.UUID, db: AsyncSession)-> User | None:
    result = await db.execute(select(User).where(User.id==user_id))
    return result.scalar_one_or_none()

async def mark_user_verified(user: User, db: AsyncSession)->None:
    user.is_verified= True
    await db.flush()

async def update_user_status(user_id: uuid.UUID, is_active: bool,  db: AsyncSession)->None:
    await db.execute(update(User).where(User.id==user_id).values(is_active=is_active))
    await db.flush()

async def hard_delete_user_by_id(user_id: uuid.UUID, db: AsyncSession)->None:
    await db.execute(delete(User).where(User.id==user_id))
    await db.flush()