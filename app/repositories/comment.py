from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.comment import Comment
from app.repositories.result_types import RepoResult, RepoStatus

    
class CommentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def get_comments(
        self,
        *, 
        post_id: int,
        limit: int,
        offset: int
    ) -> list[Comment]:
        result = await self.db.execute(
            select(Comment)
            .where(Comment.post_id == post_id)
            .options(selectinload(Comment.user))
            .order_by(Comment.created_at.asc())
            .limit(limit)
            .offset(offset)
        )
        
        return result.scalars().all()
        
    async def get_comment_by_parent_id(
        self,        
        *,
        parent_id: int
    ) -> Comment | None:
        """
        대댓글 작성을 위한 부모 댓글 조회
        """
        return await self.db.scalar(
            select(Comment)
            .where(Comment.id == parent_id, Comment.is_deleted.is_(False))
        )

    # ----------------------------------------------------------------
    # Create / Update Operations
    # ----------------------------------------------------------------
    async def add_comment(
        self,
        *,
        post_id: int,
        parent_id: int,
        user_id: int,
        content: str,           
    ) -> Comment:        
        comment = Comment(
            post_id=post_id,
            user_id=user_id,
            parent_id=parent_id,
            content=content,
        )
        
        self.db.add(comment)
        await self.db.flush()

        await self.db.refresh(comment, attribute_names=["user"])

        return comment
    
    async def update_comment_core(
        self,
        *,
        comment_id: int,
        user_id: int,
        content: str,
    ) -> RepoResult:
        vals = {
            "content": content,
            "updated_at": datetime.now(timezone.utc)
        }        
        
        stmt = (
            update(Comment)
            .where(
                Comment.id == comment_id, 
                Comment.user_id == user_id,
                Comment.is_deleted.is_(False)
            )
            .values(**vals)
            .returning(Comment)
        )
        result = await self.db.execute(stmt)
        
        updated_comment = result.scalar_one_or_none()        
        if updated_comment:
            await self.db.refresh(updated_comment, attribute_names=["user"])
            return RepoResult(RepoStatus.SUCCESS, updated_comment)
        
        stmt = (
            select(Comment.user_id, Comment.is_deleted)
            .where(Comment.id == comment_id)
        )
        result = await self.db.execute(stmt)
                
        row = result.first()
        
        if row is None:
            return RepoResult(RepoStatus.NOT_FOUND, None)
        if row.is_deleted:
            return RepoResult(RepoStatus.NOT_FOUND, None)          
        return RepoResult(RepoStatus.FORBIDDEN, None)

    # ----------------------------------------------------------------
    # Delete Operations
    # ----------------------------------------------------------------
    async def soft_delete_comment_core(
       self,
        *,
        comment_id: int,
        user_id: int, 
    ) -> RepoResult:
        now = datetime.now(timezone.utc)
        stmt = (
            update(Comment)
            .where(
                Comment.id == comment_id, 
                Comment.user_id == user_id,
                Comment.is_deleted.is_(False)
            )
            .values(
                is_deleted = True,
                updated_at = now
            )
            .returning(Comment.id)
        )
        result = await self.db.execute(stmt)

        if result.one_or_none() is not None:
            return RepoResult(RepoStatus.SUCCESS)

        return await self._analyze_failure(comment_id, user_id)

    #----------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------
    async def _analyze_failure(self, comment_id: int, user_id: int) -> RepoResult:
        """실패 원인 상세 분석"""
        stmt = select(Comment.user_id, Comment.is_deleted).where(Comment.id == comment_id)
        row = (await self.db.execute(stmt)).first()

        if row is None:
            return RepoResult(RepoStatus.NOT_FOUND)
        if row.is_deleted:
            return RepoResult(RepoStatus.ALREADY_DELETED)
        if row.user_id != user_id:
            return RepoResult(RepoStatus.FORBIDDEN)
        return RepoResult(RepoStatus.NOT_FOUND)