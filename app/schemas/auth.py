from typing import Annotated

from pydantic import AfterValidator, BaseModel, EmailStr, Field

from app.models.user import UserRole

NormalizedEmail = Annotated[EmailStr, AfterValidator(str.lower)]

class RegisterRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=128)

class RegisterResponse(BaseModel):
    message: str = "Check your email to verify your account."

class LoginRequest(BaseModel):
    email: NormalizedEmail
    password: str = Field(min_length=8, max_length=128)

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutRequest(BaseModel):
    refresh_token: str

class LogoutAllRequest(BaseModel):
    refresh_token: str


class VerifyEmailResponse(BaseModel):
    message: str="Email verified successfully"

class ResendVerificationRequest(BaseModel):
    email: NormalizedEmail

class ResendVerificationResponse(BaseModel):
    message: str = "Email resent, please check your inbox"

class ForgotPasswordRequest(BaseModel):
    email: NormalizedEmail
class ForgotPasswordResponse(BaseModel):
    message: str = "If that email exists, a reset link has ben sent."
class ResetPasswordRequest(BaseModel):
    token: str
    password: str = Field(min_length=8, max_length=128)
class ResetPasswordResponse(BaseModel):
    message: str = "Password reset successfully"

class UpdateUserStatusRequest(BaseModel):
    is_active: bool

class UpdateUserRoleRequest(BaseModel):
    role: UserRole
