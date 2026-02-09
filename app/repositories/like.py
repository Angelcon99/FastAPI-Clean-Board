from sqlalchemy import select, func, delete, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.like import Like
from app.models.post import Post

class LikeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def exists_like(
        self, 
        *, 
        post_id: int, 
        user_id: int
    ) -> bool:
        return await self.db.scalar(
            select(Like.id).where(Like.post_id == post_id, Like.user_id == user_id)
        ) is not None
    
    async def get_count_likes(
        self,
        *, 
        post_id: int
    ) -> int:
        return await self.db.scalar(
            select(func.count(Like.id)).where(Like.post_id == post_id)
        ) or 0
    
    async def get_cached_count_likes(
        self, 
        *,
        post_id: int
    ) -> int:
        return await self.db.scalar(
            select(Post.likes_count).where(Post.id == post_id)
        ) or 0

    # ----------------------------------------------------------------
    # Create / Update Operations
    # ----------------------------------------------------------------
    async def like_with_counter_cache(
        self, 
        *, 
        post_id: int, 
        user_id: int
    ) -> tuple[bool, int]:        
        ins = (
            insert(Like)
            .values(post_id=post_id, user_id=user_id)
            .on_conflict_do_nothing(index_elements=[Like.post_id, Like.user_id])
            .returning(Like.id)
        )
        
        created_id = await self.db.scalar(ins)
        if created_id is None:            
            return False, await self.get_cached_count_likes(post_id=post_id)

        # Post 테이블의 likes_count를 원자적(Atomic)으로 증가시켜 동시성 이슈 방지
        new_count = await self.db.scalar(
            update(Post)
            .where(Post.id == post_id)
            .values(likes_count=Post.likes_count + 1)
            .returning(Post.likes_count)
        )
        return True, int(new_count)

    async def like_without_counter_cache(
        self,
        *,
        post_id: int, 
        user_id: int
    ) -> tuple[bool, int]:
        ins = (
            insert(Like)
            .values(post_id=post_id, user_id=user_id)
            .on_conflict_do_nothing(index_elements=[Like.post_id, Like.user_id])
            .returning(Like.id)
        )
        created_id = await self.db.scalar(ins)
        created = created_id is not None

        new_count = await self.get_count_likes(post_id=post_id)
        return created, new_count

    # ----------------------------------------------------------------
    # Delete Operations
    # ----------------------------------------------------------------
    async def unlike_with_counter_cache(
        self, 
        *, 
        post_id: int, 
        user_id: int
    ) -> tuple[bool, int]:
        deleted_id = await self.db.scalar(
            delete(Like)
            .where(Like.post_id == post_id, Like.user_id == user_id)
            .returning(Like.id)
        )
        
        if deleted_id is None:
            return False, await self.get_cached_count_likes(post_id=post_id)
        
        real_count = await self.get_count_likes(post_id=post_id)
        
        await self.db.execute(
            update(Post)
            .where(Post.id == post_id)
            .values(likes_count=real_count)
        )

        return True, real_count
    
    async def unlike_without_counter_cache(
        self,
        *, 
        post_id: int,
        user_id: int
    ) -> tuple[bool, int]:
        deleted_id = await self.db.scalar(
            delete(Like)
            .where(Like.post_id == post_id, Like.user_id == user_id)
            .returning(Like.id)
        )
        
        removed = deleted_id is not None
        new_count = await self.get_count_likes(post_id=post_id)
        return removed, new_count