from pydantic import BaseModel, Field, EmailStr, ConfigDict

from app.core.enums import UserRole


class UserResponse(BaseModel):
    id: int    
    email: EmailStr
    nickname: str
    role: UserRole = UserRole.USER
    display_name: str | None = None
    model_config = ConfigDict(from_attributes=True)

class UserUpdate(BaseModel):
    pass

class UserPublic(BaseModel):
    nickname: str | None = None
    role: UserRole = UserRole.USER    
    model_config = ConfigDict(from_attributes=True)
    
class UserRegister(BaseModel):
    email: EmailStr = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=6, max_length=100)
    nickname: str = Field(..., min_length=1, max_length=80)