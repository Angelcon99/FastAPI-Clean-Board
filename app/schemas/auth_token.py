from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.core.enums import UserRole


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Access token (JWT)")
    refresh_token: str | None = Field(None, description="Refresh token (JWT)")
    token_type: str = Field("bearer", description="Token type")
    
class TokenPayload(BaseModel):
    sub: str = Field(..., description="User ID subject")
    role: UserRole = Field(..., description="User role (admin, user)")
    type: str = Field(..., description="Token type (access, refresh)")
    exp: datetime = Field(..., description="Expiration time (UTC)")

class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=100)

class RefreshTokenRequest(BaseModel):
    refresh_token: str
    
class LogoutRequest(BaseModel):
    refresh_token: str