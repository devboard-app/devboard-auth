from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from sqlalchemy import  select
from sqlalchemy.exc import IntegrityError
from app.exceptions import EmailAlreadyExistsException, UnexpectedException
import uuid

async def insert_user(user_email: str, user_hashed_password: str, db: AsyncSession)-> User:
    try:
        user = User(email=user_email, hashed_password=user_hashed_password, is_verified=True)
        db.add(user)
        await db.commit()
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