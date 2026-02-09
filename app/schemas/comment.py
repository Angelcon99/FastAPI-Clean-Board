from pydantic import BaseModel, ConfigDict
from datetime import datetime

from app.schemas.user import UserPublic


class CommentPublic(BaseModel):
    id: int
    post_id: int
    user_id: int
    parent_id: int | None
    content: str
    created_at: datetime
    updated_at: datetime
    user: UserPublic
    model_config = ConfigDict(from_attributes=True)

class CommentCreate(BaseModel):        
    post_id: int
    parent_id: int | None = None
    content: str

class CommentUpdate(BaseModel):
    content: str    