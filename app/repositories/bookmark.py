from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import selectinload

from app.models.bookmark import Bookmark
from app.models.post import Post


class BookmarkRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def exists(
        self,
        *,
        post_id: int,
        user_id: int,
    ) -> bool:
        """
        북마크 존재 여부 확인
        """
        return await self.db.scalar(
            select(Bookmark)
            .where(
                Bookmark.post_id == post_id, 
                Bookmark.user_id == user_id
            )
        ) is not None

    async def list_by_user(
            self,
            *,
            user_id: int,
            offset: int = 0,
            limit: int = 20,
    ) -> list[Post]:
        """
        사용자가 북마크한 게시글 목록
        """
        stmt = (
            select(Post)
            .join(Bookmark, Bookmark.post_id == Post.id)
            .where(
                Bookmark.user_id == user_id,
                Post.is_deleted.is_(False),
            )
            .order_by(Bookmark.created_at.desc())
            .offset(offset)
            .limit(limit)
            .options(selectinload(Post.author))
        )

        result = await self.db.scalars(stmt)
        return list(result)

    # ----------------------------------------------------------------
    # Create / Update Operations
    # ----------------------------------------------------------------
    async def regist(
        self,
        *,
        post_id: int,
        user_id: int
    ) -> bool:
        stmt = (
            insert(Bookmark)
            .values(post_id=post_id, user_id=user_id)
            .on_conflict_do_nothing(
                index_elements=[Bookmark.post_id, Bookmark.user_id]
            )
            .returning(Bookmark.id)
        )
        
        created_id = await self.db.scalar(stmt)
        return created_id is not None

    # ----------------------------------------------------------------
    # Delete Operations
    # ----------------------------------------------------------------
    async def remove(
        self,
        *,
        post_id: int,
        user_id: int,
    ) -> bool:
        stmt = (
            delete(Bookmark)
            .where(
                Bookmark.post_id == post_id,
                Bookmark.user_id == user_id
            )
            .returning(Bookmark.id)
        )
        
        removed_id = await self.db.scalar(stmt)
        return removed_id is not None