from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer

from app.core.redis import get_redis
from app.db.session import async_session_factory
from app.core.uow import UnitOfWork
from app.exceptions.types import InvalidTokenException, RuleViolationException
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.services.bookmark_service import BookmarkService
from app.services.comment_service import CommentService
from app.services.post_service import PostService


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/v1/auth/login", auto_error=False)

def get_uow() -> UnitOfWork:
    return UnitOfWork(session_factory=async_session_factory)

def get_post_service() -> PostService:    
    return PostService(session_factory=async_session_factory, redis_client=get_redis())

def get_comment_service() -> CommentService:
    return CommentService()

def get_auth_service() -> AuthService:
    return AuthService()

def get_bookmark_service() -> BookmarkService:
    return BookmarkService()

async def get_current_user(
    uow: UnitOfWork = Depends(get_uow),
    token: str = Depends(oauth2_scheme),
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse:
    return await svc.authenticate_user(uow, token=token)

async def get_current_user_optional(
    uow: UnitOfWork = Depends(get_uow),
    token: str | None = Depends(oauth2_scheme_optional),
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse | None:
    if not token:
        return None

    try:
        return await svc.authenticate_user(uow, token=token)
    except InvalidTokenException:
        return None

async def require_admin(
    current_user: UserResponse = Depends(get_current_user),
) -> UserResponse:
    if current_user.role != "admin":        
        raise RuleViolationException(            
            rule_code="ADMIN_ONLY",
            details={
                "required_role": "admin",
                "current_role": current_user.role,
                "user_id": current_user.id,
            }
        )
    return current_user   

__all__ = [
    "get_uow",
    
    "get_post_service",
    "get_comment_service",
    "get_auth_service",
    "get_bookmark_service",
    
    "get_current_user",
    "get_current_user_optional",
    "require_admin",
]