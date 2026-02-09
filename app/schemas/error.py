from pydantic import BaseModel, Field
from typing import Any, Optional


class ErrorResponse(BaseModel):
    code: Optional[str] = Field(None, description="에러 식별 코드")
    message: str = Field(..., description="에러 메세지")
    details: Optional[Any] = Field(None, description="에러 상세 데이터")
    trace_id: Optional[str] = Field(None, description="로그 추적을 위한 고유 ID")
