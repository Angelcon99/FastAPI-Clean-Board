from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

from app.core.enums import PostCategory
from app.schemas.comment import CommentPublic
from app.schemas.user import UserPublic


class PostSummary(BaseModel):
    id: int    
    title: str    
    category: PostCategory | None = None    
    views: int
    likes_count: int
    updated_at: datetime
    author: UserPublic
    model_config = ConfigDict(from_attributes=True)

class PostDetailCore(BaseModel):
    id: int
    title: str
    content: str
    category: PostCategory | None
    views: int
    likes_count: int
    created_at: datetime
    updated_at: datetime
    author: UserPublic
    model_config = ConfigDict(from_attributes=True)

class PostDetail(PostDetailCore):
    comments: list[CommentPublic]    
    liked_by_me: bool
    
class PostCreate(BaseModel):
    title: str  = Field(..., min_length=1, max_length=120)
    content: str = Field(..., min_length=1, max_length=10000)
    category: Optional[PostCategory] = None
    
class PostUpdate(BaseModel):
    title: Optional[str] = Field(min_length=1, max_length=120)
    content: Optional[str] = Field(default=None, max_length=1000)
    category: PostCategory | None = None    
