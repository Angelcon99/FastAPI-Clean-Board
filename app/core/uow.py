from app.repositories.bookmark import BookmarkRepository
from app.repositories.comment import CommentRepository
from app.repositories.like import LikeRepository
from app.repositories.post import PostRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.user import UserRepository


class UnitOfWork:
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.session = None

    async def __aenter__(self):
        self.session = self.session_factory()
        self.posts = PostRepository(self.session)
        self.comments = CommentRepository(self.session)
        self.likes = LikeRepository(self.session)
        self.users = UserRepository(self.session)
        self.refresh_tokens = RefreshTokenRepository(self.session)
        self.bookmarks = BookmarkRepository(self.session)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        try:
            if exc:
                await self.session.rollback()
            else:
                await self.session.commit()
        finally:
            await self.session.close()