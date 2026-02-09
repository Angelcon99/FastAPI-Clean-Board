from fastapi import APIRouter, BackgroundTasks, Depends, Query, status

from app.api.dependency import (
    get_uow,
    get_post_service,
    get_current_user,
    get_current_user_optional,
    require_admin,
)
from app.core.enums import PostCategory
from app.core.settings import settings
from app.schemas.comment import CommentPublic
from app.schemas.error import ErrorResponse
from app.schemas.like import LikeResult
from app.schemas.post import PostCreate, PostDetail, PostSummary, PostUpdate, PostDetailCore
from app.schemas.user import UserResponse
from app.core.uow import UnitOfWork
from app.services.post_service import PostService


router = APIRouter(
    prefix="/v1/posts",
    tags=["Posts"]
)

@router.get(
    "/{post_id}",
    response_model=PostDetail,
    status_code=status.HTTP_200_OK,
    summary="게시글 상세 조회",
    description="post_id로 상세 정보를 조회합니다."
)
async def read_post(
    post_id: int,
    background_tasks: BackgroundTasks,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse | None = Depends(get_current_user_optional),
    svc: PostService = Depends(get_post_service),
) -> PostDetail:    
    use_cache = settings.USE_VIEWS_COUNTER_CACHE and not settings.TESTING
    
    post = await svc.read_post_by_id(
        uow,
        post_id=post_id,
        user_id=request_user.id if request_user else None,
        use_views_counter_cache=use_cache   
    )

    if use_cache:
        background_tasks.add_task(
            svc.increment_views_background, 
            post_id=post_id
        )
        
    return post

@router.get(
    "/",
    response_model=list[PostSummary],
    status_code=status.HTTP_200_OK,
    summary="게시글 목록 조회",
    description="카테고리, 제목, 내용, 작성자 필터 및 페이징 처리를 하여 게시글 목록을 조회합니다."
)
async def read_posts_list(
    category: PostCategory | None = Query(None, description="카테고리 필터"),
    title: str | None = Query(None, description="제목 검색어"),
    content: str | None = Query(None, description="내용 검색어"),
    author: str | None = Query(None, description="작성자 닉네임"),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    uow: UnitOfWork = Depends(get_uow),
    svc: PostService = Depends(get_post_service),
) -> list[PostSummary]:
    posts = await svc.read_post_list(
        uow, 
        category=category,
        search_title=title,
        search_content=content,
        author=author,
        offset=offset,
        limit=limit
    )
    return posts

@router.post(
    "/",
    response_model=PostSummary,
    status_code=status.HTTP_201_CREATED,
    summary="게시글 작성",
    description="제목과 내용, 카테고리를 입력받아 새로운 게시글을 생성합니다."
)
async def create_post(
    body: PostCreate,    
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: PostService = Depends(get_post_service),    
) -> PostSummary:
    post = await svc.create_post(
        uow,
        user_id=request_user.id,
        data=body,
    )
    return post

@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="게시글 삭제",
    description="자신이 작성한 게시글을 삭제합니다. (Soft Delete)"
)
async def delete_post(
    post_id: int,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: PostService = Depends(get_post_service),
) -> None:
    await svc.soft_delete_post(
        uow,
        post_id=post_id,
        user_id=request_user.id,
    )

@router.get(
    "/admin",
    summary="관리자 테스트용",
    description="관리자 권한(Admin Role)이 있는지 확인하는 테스트 API입니다."
)
async def admin_ex(current_user=Depends(require_admin)):
    return {"message": "Welcome, admin!"}

@router.put(
    "/{post_id}/like",
    status_code=status.HTTP_200_OK,
    summary="게시글 좋아요 토글",
    description="게시글에 좋아요를 누르거나, 이미 누른 경우 취소합니다."
)
async def toggle_like_post(
    post_id: int,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: PostService = Depends(get_post_service),
) -> LikeResult:
    liked, count = await svc.toggle_like_post(
        uow,
        post_id=post_id,
        user_id=request_user.id,
    )
    return LikeResult(liked=liked, likes_count=count)

@router.patch(
    "/{post_id}",
    response_model=PostDetailCore,
    status_code=status.HTTP_200_OK,
    summary="게시글 수정",
    description="자신이 작성한 게시글을 수정합니다."
)
async def update_post(
    post_id: int,
    body: PostUpdate,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: PostService = Depends(get_post_service),
) -> PostDetailCore:
    result = await svc.update_post_core(
        uow,
        post_id=post_id,
        user_id=request_user.id,
        data=body,
    )    
    return result

@router.get(
    "/{post_id}/comments",
    response_model=list[CommentPublic],
    status_code=status.HTTP_200_OK,
    summary="게시글 댓글 조회",
    description="post_id 게시글에 달린 댓글 목록을 조회합니다."
)
async def read_comments(
    post_id: int,
    limit: int = Query(50, ge=20, le=100),
    offset: int = Query(0, ge=0),
    uow: UnitOfWork = Depends(get_uow),
    svc: PostService = Depends(get_post_service),
) -> list[CommentPublic]:
    comments = await svc.get_comments_for_post(
        uow, 
        post_id=post_id, 
        limit=limit, 
        offset=offset
    )
    return comments

@router.post(
    "/{post_id}/bookmark",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="게시글 북마크 토글",
    description="게시글을 북마크하거나, 이미 북마크한 경우 취소합니다."
)
async def toggle_bookmark_post(
    post_id: int,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: PostService = Depends(get_post_service),
) -> None:
    await svc.toggle_bookmark_to_post(
        uow,
        post_id=post_id,
        user_id=request_user.id
    )