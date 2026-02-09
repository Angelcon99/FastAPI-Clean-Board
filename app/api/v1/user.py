from fastapi import APIRouter, Depends, Query, status

from app.api.dependency import (
    get_uow,
    get_current_user,
    get_bookmark_service
)
from app.core.uow import UnitOfWork
from app.schemas.post import PostSummary
from app.schemas.user import UserResponse
from app.services.bookmark_service import BookmarkService


router = APIRouter(
    prefix="/v1/users",
    tags=["Users"],
)

@router.get(
    "/me/bookmarks",
    response_model=list[PostSummary],
    status_code=status.HTTP_200_OK,
    summary="내 북마크 조회",
    description="사용자가 북마크한 게시글 목록을 조회합니다."
)
async def read_my_bookmarks(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=20, le=100),    
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: BookmarkService = Depends(get_bookmark_service),   
) -> list[PostSummary]:
    posts = await svc.read_my_bookmarks(
        uow,
        user_id=request_user.id,
        offset=offset,
        limit=limit
    )
    return posts