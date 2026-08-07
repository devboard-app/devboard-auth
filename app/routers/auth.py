from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import oauth2_scheme
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    LogoutRequest,
    RefreshTokenRequest,
    RefreshTokenResponse,
    RegisterRequest,
    RegisterResponse,
    ResendVerificationRequest,
    ResendVerificationResponse,
    VerifyEmailResponse,
)
from app.services.auth import login, logout, logout_all, refresh, register
from app.services.auth import resend_verification as resend
from app.services.auth import verify_email as verify

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register_user( request: RegisterRequest, db: AsyncSession = Depends(get_db)):
    await register(request.email, request.password,db)
    return RegisterResponse()

@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
async def login_user(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    jwt_token, raw_refresh_token = await login(request.email, request.password, db)
    return LoginResponse(access_token=jwt_token, refresh_token=raw_refresh_token)


@router.post("/refresh-token", response_model=RefreshTokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(request: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    new_jwt_token, new_raw_refresh_token= await refresh(request.refresh_token, db)
    return RefreshTokenResponse(access_token = new_jwt_token, refresh_token=new_raw_refresh_token)


@router.post("/logout", status_code = status.HTTP_204_NO_CONTENT)
async def logout_user(request: LogoutRequest, db: AsyncSession = Depends(get_db)):
    await logout(request.refresh_token, db)


@router.post("/logout-all", status_code= status.HTTP_204_NO_CONTENT)
async def logout_all_user(credentials = Depends(oauth2_scheme), db: AsyncSession = Depends(get_db)):
    await logout_all(credentials.credentials, db)

@router.get("/verify-email", response_model= VerifyEmailResponse, status_code= status.HTTP_200_OK)
async def verify_email(token: str = Query(...), db: AsyncSession = Depends(get_db)):
    await verify(token, db)
    return VerifyEmailResponse()

@router.post("/resend-verification", response_model=ResendVerificationResponse, status_code = status.HTTP_200_OK)
async def resend_verification(request: ResendVerificationRequest, db: AsyncSession = Depends(get_db)):
    await resend(request.email, db)
    return ResendVerificationResponse()