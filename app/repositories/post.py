from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import insert, or_, select, update
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.enums import PostCategory
from app.models.post import Post
from app.models.user import User
from app.repositories.result_types import RepoResult, RepoStatus


class PostRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def exists(
            self,
            *,
            post_id: int
    ) -> bool:
        """
        가벼운 게시글 존재 여부 확인
        """
        query = select(1).where(Post.id == post_id).limit(1)
        result = await self.db.execute(query)
        return result.scalar() is not None

    async def get_post(
        self, 
        *, 
        post_id: int
    ) -> Post | None:        
        return await self.db.scalar(
            select(Post).where(Post.id == post_id, Post.is_deleted.is_(False))
        )

    async def get_post_with_user(
        self,
        *,
        post_id: int
    ) -> Post | None:
        return await self.db.scalar(
            select(Post)
            .options(selectinload(Post.author))
            .where(Post.id == post_id, Post.is_deleted.is_(False))
        )

    async def get_posts_list(
        self, 
        *,
        category: PostCategory | None,
        search_title: str | None,
        search_content: str | None,
        author: str | None,
        offset: int,
        limit: int
    ) -> list[Post]:
        """
        필터링 및 페이징 목록 조회
        """
        query = (
            select(Post)
            .options(selectinload(Post.author))
            .join(User, User.id == Post.user_id)
            .where(Post.is_deleted.is_(False))
            .order_by(Post.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        # 카테고리 필터
        if category:
            query = query.where(Post.category == category)

        # 간단한 검색 (검색 데이터가 많아지면 느려질 수 있음)
        # TODO: TSVector(Full Text Search) 고려
        if search_title:
            query = query.where(Post.title.ilike(f"%{search_title}%"))

        if search_content:
            query = query.where(Post.content.ilike(f"%{search_content}%"))

        if author:
            query = query.where(User.nickname.ilike(f"%{author}%"))
            
        result = await self.db.execute(query)
        return result.scalars().all()

    # ----------------------------------------------------------------
    # Create / Update Operations
    # ----------------------------------------------------------------
    async def create_post(
            self,
            *,
            author_id: int,
            title: str,
            content: str,
            category: Optional[PostCategory]
    ) -> Post:
        stmt = (
            insert(Post)
            .values(
                user_id=author_id,
                title=title,
                content=content,
                category=category,
            )
            .returning(Post)
            .options(selectinload(Post.author))
        )

        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def update_post_core(
            self,
            *,
            post_id: int,
            user_id: int,
            title: str,
            content: str,
            category: Optional[PostCategory]
    ) -> RepoResult:
        vals = {}
        if title is not None:
            vals["title"] = title
        if content is not None:
            vals["content"] = content
        if category is not None:
            vals["category"] = category
        vals["updated_at"] = datetime.now(timezone.utc)

        stmt = (
            update(Post)
            .where(Post.id == post_id, Post.user_id == user_id, Post.is_deleted.is_(False))
            .values(**vals)
            .returning(Post)
            .options(selectinload(Post.author))
        )
        result = await self.db.execute(stmt)

        updated_post = result.scalar_one_or_none()
        if updated_post:
            return RepoResult(RepoStatus.SUCCESS, updated_post)

        return await self._analyze_failure(post_id, user_id)

    async def sync_views(
            self,
            *,
            post_id: int,
            views: int
    ) -> None:
        """
        Redis 조회수 DB 동기화
        """
        stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(views=views)
        )
        await self.db.execute(stmt)

    async def increment_views_if_exists(self, *, post_id: int) -> int | None:
        """
        조회수 원자적 증가
        """
        stmt = (
            update(Post)
            .where(Post.id == post_id, Post.is_deleted.is_(False))
            .values(views=Post.views + 1)
            .returning(Post.views)
        )
        return await self.db.scalar(stmt)

    # ----------------------------------------------------------------
    # Delete Operations
    # ----------------------------------------------------------------
    async def soft_delete_post(
        self,
        *,
        post_id: int
    ) -> None:
        """
        관리자용 강제 삭제
        """
        await self.db.execute(
            update(Post).where(Post.id == post_id).values(is_deleted=True)
        )

    async def soft_delete_post_core(
        self,
        *,
        post_id: int, 
        user_id: int
    ) -> RepoResult:
        """
        본인 게시글 삭제
        """
        now = datetime.now(timezone.utc)
        stmt = (
            update(Post)
            .where(
                Post.id == post_id,
                Post.user_id == user_id,
                Post.is_deleted.is_(False),
            )
            .values(
                is_deleted=True,
                updated_at=now,
            )
            .returning(Post.id)
        )
        result = await self.db.execute(stmt)
        deleted = result.one_or_none()
        if deleted is not None:
            return RepoResult(RepoStatus.SUCCESS)
        
        return await self._analyze_failure(post_id, user_id)

    # ----------------------------------------------------------------
    # Helper Methods
    # ----------------------------------------------------------------
    async def _analyze_failure(
            self,
            post_id: int,
            user_id: int
    ) -> RepoResult:
        """
        실패 원인 분석
        """
        stmt = (
            select(Post.user_id, Post.is_deleted).
            where(Post.id == post_id)
        )
        result = await self.db.execute(stmt)

        row = result.first()

        if row is None:
            return RepoResult(RepoStatus.NOT_FOUND)
        if row.is_deleted:
            return RepoResult(RepoStatus.ALREADY_DELETED)
        if row.user_id != user_id:
            return RepoResult(RepoStatus.FORBIDDEN)

        return RepoResult(RepoStatus.NOT_FOUND)