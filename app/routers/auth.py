from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import text
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, RefreshTokenRequest, RefreshTokenResponse, LogoutRequest
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import CreateUserError, check_email_exists, create_user, get_user_by_email, get_user_by_id, logout_user, logout_all_user
from app.services.password import hash_password, verify_password
from app.services.jwt import create_access_token, create_refresh_token, search_refresh_token_in_db, decode_access_token
import uuid

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user( request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    if await check_email_exists(request.email, db):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
    
    hashed_password = hash_password(request.password)

    user, error = await create_user(request.email, hashed_password, db)
    if user is None:
        if error == CreateUserError.CONFLICT:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Failed to create user")
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unexpected error occurred")

    ## TODO: generate a verification token to send to the user on email
    ## store token with 24h expiration (verification_tokens table)
    ## send email
    ## WILL BE IMPLEMENTED WHEN EMAIL SERVICE IS READY
    
    return RegisterResponse()

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    user = await get_user_by_email(request.email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")
    if user.is_active is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is inactive")
    if user.is_verified is False:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is not verified")

    jwt_token = create_access_token(user_id=str(user.id), email=user.email, role=str(user.role))
    raw_refresh_token = await create_refresh_token(user_id=user.id, db=db)
    if not raw_refresh_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred while generating refresh token")
    return LoginResponse(access_token=jwt_token, refresh_token=raw_refresh_token)


@router.post("/refresh-token", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    search_token_found = await search_refresh_token_in_db(request.refresh_token, db)
    if search_token_found is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid or expired")
    
    user = await get_user_by_id(search_token_found.user_id, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalid or expired")

    new_raw_refresh_token= None
    try:
        search_token_found.revoked = True
        new_raw_refresh_token = await create_refresh_token(user_id=user.id, db=db, commit=False)
        await db.commit()
    except Exception:
        await db.rollback()
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")
    if not new_raw_refresh_token:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An unexpected error occurred")
    
    new_jwt_token = create_access_token(user_id= str(user.id) ,email=user.email, role=str(user.role))
    return RefreshTokenResponse(access_token = new_jwt_token, refresh_token=new_raw_refresh_token)


# TODO: handle concurent request 
# TODO: Implement logout endpoint POST /auth/logout
@router.post("/logout", status_code = status.HTTP_204_NO_CONTENT)
async def logout(request: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await logout_user(request.refresh_token, db)


@router.post("/logout-all", status_code= status.HTTP_204_NO_CONTENT)
async def logout_all(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login")), db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_access_token(token)
        user_id = uuid.UUID(payload["sub"])
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")

    await logout_all_user(user_id,db)