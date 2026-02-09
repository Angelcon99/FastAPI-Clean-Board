from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.core.settings import settings
from app.api.v1 import auth, comment, post, user
from app.core.logging import setup_logging
from app.exceptions.handlers import register_exception_handlers
from app.middlewares.access_log import AccessLogMiddleware
from app.middlewares.timing_log import TimingLogMiddleware
from app.middlewares.trace import TraceIdASGIMiddleware


setup_logging()

description = """
### FastAPI Board 프로젝트 

이 프로젝트는 **FastAPI**를 기반으로 구축된 게시판 서버입니다.
유지보수와 확장성을 고려한 서버를 설계하는 데 중점을 두었습니다.

## 기능 요약
* **게시글**: 작성, 수정, 삭제, 페이징, 검색
* **댓글**: 계층형 대댓글 지원
* **인증**: JWT + Refresh Token Rotation 도입
"""

tags_metadata = [
    {
        "name": "Auth",
        "description": "사용자 인증, 토큰 발급 및 갱신(Rotation) 로직",
    },
    {
        "name": "Users",
        "description": "회원가입, 내 정보 조회 및 수정",
    },
    {
        "name": "Posts",
        "description": "게시글 CRUD, 조회수 증가, 검색 및 필터링",
    },
    {
        "name": "Comments",
        "description": "댓글 및 대댓글 작성/수정/삭제",
    },
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    description=description,
    version=settings.VERSION,
    openapi_tags=tags_metadata,
)

origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://localhost:3000",
    "http://localhost:8080",
    "https://localhost:8080",
]

# Logging
app.add_middleware(AccessLogMiddleware)
app.add_middleware(TimingLogMiddleware)
# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# Trace id
app.add_middleware(TraceIdASGIMiddleware)

# Router
app.include_router(post.router)
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(comment.router)


# Exception Handler
register_exception_handlers(app)

if __name__ == "__main__":    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )