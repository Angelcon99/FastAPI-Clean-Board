from app.core.uow import UnitOfWork
from app.schemas.post import PostSummary


class BookmarkService:
    async def read_my_bookmarks(
        self,
        uow: UnitOfWork,
        *,
        user_id: int,
        offset: int,
        limit: int              
    ) -> list[PostSummary]:
        """
        사용자가 북마크한 게시글 목록 조회
        """
        async with uow:
            bookmarks_post = await uow.bookmarks.list_by_user(
                user_id=user_id,
                offset=offset,
                limit=limit
            )

            return [PostSummary.model_validate(bookmark_post) for bookmark_post in bookmarks_post]