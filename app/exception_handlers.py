# app/exception_handlers.py
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.exceptions import (
    EmailAlreadyExistsException,
    UserNotFoundException,
    InvalidCredentialsException,
    UnexpectedException,
    UserInactiveException,
    UserNotVerifiedException,
    InvalidAccessTokenException,
    InvalidTokenException,
    TokenExpiredException,
    EmailServiceException,
)

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(EmailAlreadyExistsException)
    async def email_exists_handler(request, exc):
        return JSONResponse(status_code=409, content={"detail": "Email already registered"})

    @app.exception_handler(UserNotFoundException)
    async def user_not_found_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": "User not found"})

    @app.exception_handler(InvalidCredentialsException)
    async def invalid_credentials_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Invalid credentials"})

    @app.exception_handler(UnexpectedException)
    async def unexpected_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Unexpected error occurred"})

    @app.exception_handler(UserInactiveException)
    async def user_inactive_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "User account is inactive"})

    @app.exception_handler(UserNotVerifiedException)
    async def user_not_verified_handler(request, exc):
        return JSONResponse(status_code=403, content={"detail": "User account is not verified"})

    @app.exception_handler(InvalidAccessTokenException)
    async def invalid_access_token_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    @app.exception_handler(InvalidTokenException)
    async def invalid_token_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Token invalid or expired"})

    @app.exception_handler(TokenExpiredException)
    async def token_expired_handler(request, exc):
        return JSONResponse(status_code=401, content={"detail": "Token invalid or expired"})

    @app.exception_handler(EmailServiceException)
    async def email_service_handler(request, exc):
        return JSONResponse(status_code=502, content={"detail": "Email service is not working"})