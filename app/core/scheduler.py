import logging

from app.api.dependency import get_uow
from app.core.redis import get_redis
from app.core.uow import UnitOfWork
from app.db.session import async_session_factory

logger = logging.getLogger(__name__)

async def sync_post_views_to_db():
    redis_client = get_redis()

    async with redis_client:
        updates = {}

    async for key in redis_client.scan_iter("post:views:*"):
        try:
            post_id = int(key.split(":")[-1])
            views = await redis_client.get(key)
            if views:
                updates[post_id] = int(views)
        except Exception as e:
            logger.error(f"Error parsing redis key {key}: {e}")

        if not updates:
            return

        try:
            async with UnitOfWork(async_session_factory) as uow:
                for post_id, views in updates.items():
                    await uow.posts.sync_views(post_id=post_id, views=views)

        except Exception as e:
            logger.error(f"Failed to sync views to DB: {e}")