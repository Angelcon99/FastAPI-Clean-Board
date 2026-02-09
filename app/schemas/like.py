from pydantic import BaseModel, Field


class LikeResult(BaseModel):
    liked: bool = Field(...)
    likes_count: int = Field(..., ge=0)
