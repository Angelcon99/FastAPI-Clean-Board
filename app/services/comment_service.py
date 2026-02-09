from app.core.uow import UnitOfWork
from app.exceptions.types import CommentNotFoundException, CommentPostMismatchException, InternalServerException, ReplyDepthLimitExceededException, RuleViolationException, UserMismatchException
from app.repositories.result_types import RepoStatus
from app.schemas.comment import CommentCreate, CommentUpdate, CommentPublic


class CommentService:    
    async def register_comment(
        self,
        uow: UnitOfWork,
        *,        
        user_id: int,
        data: CommentCreate     
    ) -> CommentPublic:
        """
        게시글에 댓글 등록
        parent_id가 존재하면 대댓글로 등록

        Raises:
            CommentNotFoundException: 대댓글 작성 시, 지정한 부모 댓글(parent_id)이 존재하지 않는 경우
            ReplyDepthLimitExceededException: 대댓글에 또 대댓글을 달려고 하는 경우
            CommentPostMismatchException: 부모 댓글이 요청된 게시글(post_id)에 속하지 않는 경우
        """
        async with uow:
            parent_id = data.parent_id
            
            if parent_id is not None:
                parent = await uow.comments.get_comment_by_parent_id(parent_id=parent_id)
                
                if parent is None:
                    raise CommentNotFoundException(comment_id=parent_id)
                if parent.parent_id is not None:
                    raise ReplyDepthLimitExceededException(parent_id=parent_id)
                if parent.post_id != data.post_id:
                    raise CommentPostMismatchException(
                        parent_id=parent_id,
                        parent_post_id=parent.post_id,
                        request_post_id=data.post_id
                    )

            created_comment = await uow.comments.add_comment(
                post_id=data.post_id,
                parent_id=data.parent_id,
                user_id=user_id,
                content=data.content,
            )

            return CommentPublic.model_validate(created_comment)
                      
    async def update_comment(
        self,
        uow: UnitOfWork,
        *,
        comment_id: int,
        user_id: int,
        data: CommentUpdate    
    ) -> CommentPublic:
        """
        기존 댓글의 내용 수정

        Raises:
            CommentNotFoundException: 해당 댓글이 존재하지 않거나 이미 삭제된 경우
            UserMismatchException: 작성자 본인이 아닌 사용자가 수정을 시도한 경우
            InternalServerException: 예상치 못한 DB 에러 발생 시
        """
        async with uow:            
            result = await uow.comments.update_comment_core(
                comment_id=comment_id,
                user_id=user_id,
                content=data.content
            )

        if result.status == RepoStatus.SUCCESS:
            return CommentPublic.model_validate(result.data)
        if result.status == RepoStatus.NOT_FOUND:
            raise CommentNotFoundException(comment_id=comment_id)
        if result.status == RepoStatus.FORBIDDEN:
            raise UserMismatchException("작성자만 수정할 수 있습니다.")        
        raise InternalServerException()
      
    async def soft_delete_comment(
        self,
        uow: UnitOfWork,
        *,
        comment_id: int,
        user_id: int,
    ) -> None:
        """
        댓글 삭제 처리(Soft Delete)

        Raises:
            CommentNotFoundException: 해당 댓글이 존재하지 않거나 이미 삭제된 상태인 경우
            UserMismatchException: 작성자 본인이 아닌 사용자가 삭제를 시도한 경우
            InternalServerException: 예상치 못한 DB 에러 발생 시
        """
        async with uow:            
            result = await uow.comments.soft_delete_comment_core(
                comment_id=comment_id,
                user_id=user_id
            )

        if result.status == RepoStatus.SUCCESS:
            return
        if result.status in (RepoStatus.NOT_FOUND, RepoStatus.ALREADY_DELETED):
            raise CommentNotFoundException(comment_id=comment_id)
        if result.status == RepoStatus.FORBIDDEN:
            raise UserMismatchException()        
        raise InternalServerException()