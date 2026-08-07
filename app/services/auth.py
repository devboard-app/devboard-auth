
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import (
    EmailAlreadyExistsException,
    InvalidAccessTokenException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
    UserAlreadyVerifiedException,
    UserInactiveException,
    UserNotVerifiedException,
)
from app.infrastructure.email import send_verification_email
from app.repositories.token import (
    delete_all_user_tokens,
    get_refresh_token_by_hash,
    insert_new_refresh_token,
    revoke_and_insert_new_refresh_token,
    revoke_refresh_token,
)
from app.repositories.user import (
    get_user_by_email,
    get_user_by_id,
    insert_user,
    mark_user_verified,
)
from app.repositories.verification_token import (
    get_verification_token_by_hash,
    insert_verification_token,
    invalidate_user_verification_tokens,
    mark_verification_token_used,
)
from app.services.jwt import (
    create_access_token,
    decode_access_token,
    generate_refresh_token,
    generate_verification_token,
    validate_refresh_token,
)
from app.services.password import hash_password, verify_password


async def register(user_email: str, password: str, db: AsyncSession):
    user = await get_user_by_email(user_email, db)
    if user is not None:
        raise EmailAlreadyExistsException()
    hashed_password = hash_password(password)
    user = await insert_user(user_email, hashed_password, db)
    raw_verification_token, verification_token_hash = generate_verification_token()
    await insert_verification_token(user, verification_token_hash, db)
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={raw_verification_token}"
    await db.commit()
    await send_verification_email(user.email, verify_url)
    
    return user

async def login(user_email: str, password: str, db: AsyncSession):
    user = await get_user_by_email(user_email, db)
    if user is None or not verify_password(password, user.hashed_password):
        raise InvalidCredentialsException()
    if not user.is_active:
        raise UserInactiveException()
    if not user.is_verified:
        raise UserNotVerifiedException()
    raw_refresh_token, hash_refresh_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await insert_new_refresh_token(user.id, hash_refresh_token, expires_at, db)
    await db.commit()
    jwt_token = create_access_token(user_id = str(user.id), email= user.email, role=str(user.role))
    
    return jwt_token, raw_refresh_token

async def refresh(token: str, db: AsyncSession)-> tuple[str,str]:
    old_refresh_token = await validate_refresh_token(token, db)
    user = await get_user_by_id(old_refresh_token.user_id, db)
    if user is None:
        raise InvalidTokenException()
    new_raw_refresh_token, new_refresh_token_hash = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await revoke_and_insert_new_refresh_token(old_refresh_token, user.id, new_refresh_token_hash, expires_at, db)
    await db.commit()
    new_jwt_token = create_access_token(user_id = str(user.id), email=user.email, role=str(user.role))
    return new_jwt_token, new_raw_refresh_token

async def logout(token: str, db: AsyncSession)->None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    refresh_token = await get_refresh_token_by_hash(token_hash, db)
    if refresh_token is None:
        return 
    await revoke_refresh_token(refresh_token, db)
    await db.commit()

async def logout_all(token: str, db:AsyncSession)->None:
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise InvalidAccessTokenException()
    await delete_all_user_tokens(user_id, db)
    await db.commit()

async def verify_email(token: str, db: AsyncSession)->None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    verification_token = await get_verification_token_by_hash(token_hash, db)
    if verification_token is None or verification_token.used:
        raise InvalidTokenException()
    if verification_token.expires_at < datetime.now(timezone.utc):
        raise TokenExpiredException()
    user = await get_user_by_id(verification_token.user_id, db)
    if user is None:
        raise InvalidTokenException()
    await mark_user_verified(user, db)
    await mark_verification_token_used(verification_token, db)
    await db.commit()

async def resend_verification(user_email: str, db: AsyncSession)-> None:
    user = await get_user_by_email(user_email, db)
    if user is None:
        raise InvalidCredentialsException()
    if user.is_verified:
        raise UserAlreadyVerifiedException()
    raw_verification_token, verification_token_hash = generate_verification_token()
    await invalidate_user_verification_tokens(user.id, db)
    await insert_verification_token(user, verification_token_hash, db)
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={raw_verification_token}"
    await send_verification_email(user.email, verify_url)
    await db.commit()
    