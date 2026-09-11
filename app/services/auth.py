
import hashlib
import uuid
from datetime import datetime, timedelta, timezone

from redis.exceptions import RedisError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.exceptions import (
    CoreServiceException,
    EmailAlreadyExistsException,
    InvalidCredentialsException,
    InvalidTokenException,
    TokenExpiredException,
    UserInactiveException,
    UserNotFoundException,
    UserNotVerifiedException,
)
from app.infrastructure.core import sync_user_to_core
from app.infrastructure.email import send_password_reset_email, send_verification_email
from app.infrastructure.rate_limit import clear_rate_limit, rate_limit
from app.models.user import UserRole
from app.repositories.password_reset_token import (
    get_password_reset_token_by_hash,
    insert_password_reset_token,
    mark_password_reset_token_used,
)
from app.repositories.token import (
    get_refresh_token_by_hash,
    insert_new_refresh_token,
    revoke_all_user_tokens,
    revoke_and_insert_new_refresh_token,
    revoke_refresh_token,
)
from app.repositories.user import (
    get_user_by_email,
    get_user_by_id,
    hard_delete_user_by_id,
    insert_user,
    mark_user_verified,
    update_user_password,
)
from app.repositories.user import (
    update_user_role as update_user_role_repo,
)
from app.repositories.user import (
    update_user_status as update_user_status_repo,
)
from app.repositories.verification_token import (
    get_verification_token_by_hash,
    insert_verification_token,
    invalidate_user_verification_tokens,
    mark_verification_token_used,
)
from app.services.jwt import (
    create_access_token,
    generate_password_reset_token,
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
    await db.commit()
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={raw_verification_token}"
    try:
        await sync_user_to_core(str(user.id), user.email, str(user.role.value))
    except Exception:
        await hard_delete_user_by_id(user.id, db)
        await db.commit()
        raise CoreServiceException()
    await send_verification_email(user.email, verify_url)

    return user

async def login(user_email: str, password: str, db: AsyncSession, client_ip: str):
    user = await get_user_by_email(user_email, db)
    if user is None or not verify_password(password, user.hashed_password):
        try:
            await rate_limit(5, 900, f"login_ip:{client_ip}")
            await rate_limit(5, 900, f"login_email:{user_email}")
        except RedisError:
            pass
        raise InvalidCredentialsException()
    if not user.is_active:
        raise UserInactiveException()
    if not user.is_verified:
        raise UserNotVerifiedException()
    raw_refresh_token, hash_refresh_token = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await insert_new_refresh_token(user.id, hash_refresh_token, expires_at, db)
    await db.commit()
    jwt_token = create_access_token(user_id = str(user.id), email= user.email, role=str(user.role.value))

    #rate limit clear on success
    try:
        await clear_rate_limit(f"login_ip:{client_ip}")
        await clear_rate_limit(f"login_email:{user_email}")
    except RedisError:
        pass

    return jwt_token, raw_refresh_token

async def refresh(token: str, db: AsyncSession)-> tuple[str,str]:
    old_refresh_token = await validate_refresh_token(token, db)
    user = await get_user_by_id(old_refresh_token.user_id, db)
    if user is None:
        raise InvalidTokenException()
    if not user.is_active:
        raise UserInactiveException()
    new_raw_refresh_token, new_refresh_token_hash = generate_refresh_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days = settings.REFRESH_TOKEN_EXPIRE_DAYS)

    await revoke_and_insert_new_refresh_token(old_refresh_token, user.id, new_refresh_token_hash, expires_at, db)
    await db.commit()
    new_jwt_token = create_access_token(user_id = str(user.id), email=user.email, role=str(user.role.value))
    return new_jwt_token, new_raw_refresh_token

async def logout(token: str, db: AsyncSession)->None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    refresh_token = await get_refresh_token_by_hash(token_hash, db)
    if refresh_token is None:
        return 
    await revoke_refresh_token(refresh_token, db)
    await db.commit()

async def logout_all(token: str, db:AsyncSession)->None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    refresh_token = await get_refresh_token_by_hash(token_hash, db)
    if refresh_token is None:
        raise InvalidTokenException()
    await revoke_all_user_tokens(refresh_token.user_id, db)
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
        return
    if user.is_verified:
        return
    raw_verification_token, verification_token_hash = generate_verification_token()
    await invalidate_user_verification_tokens(user.id, db)
    await insert_verification_token(user, verification_token_hash, db)
    verify_url = f"{settings.FRONTEND_URL}/auth/verify-email?token={raw_verification_token}"
    await send_verification_email(user.email, verify_url)
    await db.commit()

async def update_user_status(user_id: uuid.UUID, is_active: bool, db: AsyncSession):
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise UserNotFoundException()
    if not is_active:
        await revoke_all_user_tokens(user_id, db)
    await update_user_status_repo(user_id, is_active, db)
    await db.commit()

async def update_user_role(user_id: uuid.UUID, role: UserRole, db: AsyncSession):
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise UserNotFoundException()
    await update_user_role_repo(user_id, role, db)
    await db.commit()

async def forgot_password(user_email: str, db: AsyncSession) -> None:
    user = await get_user_by_email(user_email, db)
    if user is None:
        return # return 200 no matter what
    raw_token, token_hash = generate_password_reset_token()
    await insert_password_reset_token(user, token_hash, db)
    reset_url = f"{settings.FRONTEND_URL}/auth/reset-password?token={raw_token}"
    await send_password_reset_email(user_email, reset_url)
    await db.commit()

async def reset_password(token: str, new_password: str, db: AsyncSession) -> None:
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    reset_token = await get_password_reset_token_by_hash(token_hash, db)
    if reset_token is None or reset_token.used:
        raise InvalidTokenException()
    if reset_token.expires_at < datetime.now(timezone.utc):
        raise TokenExpiredException()
    user = await get_user_by_id(reset_token.user_id, db)
    if user is None:
        raise InvalidTokenException()
    hashed_password = hash_password(new_password)
    await update_user_password(user.id, hashed_password, db)
    await mark_password_reset_token_used(reset_token, db)
    await revoke_all_user_tokens(user.id, db)
    await db.commit()