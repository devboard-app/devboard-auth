from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer
from app.schemas.auth import LoginRequest, LoginResponse, RegisterRequest, RegisterResponse, RefreshTokenRequest, RefreshTokenResponse, LogoutRequest
from app.database import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.auth import  register, login, refresh , logout, logout_all


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
async def logout_all_user(token: str = Depends(OAuth2PasswordBearer(tokenUrl="/auth/login")), db: AsyncSession = Depends(get_db)):
    await logout_all(token, db)