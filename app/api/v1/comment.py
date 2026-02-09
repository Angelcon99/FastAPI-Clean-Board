from fastapi import APIRouter, Depends, status

from app.api.dependency import (
    get_comment_service, 
    get_uow,
    get_current_user
)
from app.core.uow import UnitOfWork
from app.schemas.comment import CommentCreate, CommentPublic, CommentUpdate
from app.schemas.user import UserResponse
from app.services.comment_service import CommentService

router = APIRouter(
    prefix="/v1/comments",
    tags=["Comments"]
)

@router.post(
    "/",
    response_model=CommentPublic,
    status_code=status.HTTP_201_CREATED,
    summary="댓글 작성",
    description="게시글에 댓글을 작성합니다. 대댓글인 경우 parent_comment_id를 포함해야 합니다."
)
async def create_comment(    
    body: CommentCreate,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
) -> CommentPublic:
    comment = await svc.register_comment(
        uow,
        user_id=request_user.id,
        data=body
    )    
    return CommentPublic.model_validate(comment)

@router.patch(
    "/{comment_id}",
    response_model=CommentPublic,
    status_code=status.HTTP_200_OK,
    summary="댓글 수정",
    description="자신이 작성한 댓글을 수정합니다."
)
async def update_comment(
    comment_id: int,
    body: CommentUpdate,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
) -> CommentPublic:
    comment = await svc.update_comment(
        uow, 
        comment_id=comment_id, 
        user_id=request_user.id,
        data=body
    )    
    return CommentPublic.model_validate(comment)

@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="댓글 삭제",
    description="자신이 작성한 댓글을 삭제합니다. (Soft Delete)"
)
async def delete_comment(
    comment_id: int,
    uow: UnitOfWork = Depends(get_uow),
    request_user: UserResponse = Depends(get_current_user),
    svc: CommentService = Depends(get_comment_service),
) -> None:
    await svc.soft_delete_comment(
        uow,
        comment_id=comment_id,
        user_id=request_user.id
    )