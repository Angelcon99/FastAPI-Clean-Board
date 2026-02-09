from typing import Optional

from app.core.enums import PostCategory
from app.core.uow import UnitOfWork
from app.exceptions.types import InternalServerException, PostNotFoundException, UserMismatchException
from app.repositories.post import RepoStatus
from app.schemas.comment import CommentPublic
from app.schemas.post import PostCreate, PostDetailCore, PostUpdate, PostDetail, PostSummary


class PostService:
    def __init__(self, session_factory, redis_client):
        self.session_factory = session_factory
        self.redis = redis_client
        
    async def read_post_by_id(
        self,
        uow: UnitOfWork,
        *,
        post_id: int,
        user_id: Optional[int] = None,
        comments_limit: int = 100,
        comments_offset: int = 0,        
        use_views_counter_cache: bool = True,
    ) -> PostDetail:
        """
        게시글 상세 정보 조회

        Raises:
            PostNotFoundException: 해당 ID의 게시글이 존재하지 않는 경우
        """
        async with uow:
            if use_views_counter_cache:                
                post = await uow.posts.get_post_with_user(post_id=post_id)
                if not post:
                    raise PostNotFoundException(post_id=post_id)
                
                post_dto = PostDetailCore.model_validate(post)
                
                cache_key = f"post:views:{post_id}"
                cached_views = await self.redis.get(cache_key)

                if cached_views is not None:
                    # uow.session.expunge(post)   # 세션에서 객체 분리, 자동 커밋 방지
                    post_dto.views = int(cached_views)
                else:                    
                    await self.redis.set(cache_key, post_dto.views)
            
            else:                
                new_views = await uow.posts.increment_views_if_exists(post_id=post_id)
                if new_views is None:
                    raise PostNotFoundException(post_id=post_id)
                                
                post = await uow.posts.get_post_with_user(post_id=post_id)
                
                post_dto = PostDetailCore.model_validate(post)
                post_dto.views = new_views
            
            comments = await uow.comments.get_comments(
                post_id=post_id,
                limit=comments_limit,
                offset=comments_offset,
            )
            
            liked_by_me = False
            if user_id:
                liked_by_me = await uow.likes.exists_like(
                    post_id=post_id,
                    user_id=user_id,
                )

            return PostDetail(
                **PostDetailCore.model_validate(post_dto).model_dump(),
                comments=[CommentPublic.model_validate(c) for c in comments],
                liked_by_me=liked_by_me
            )
    
    async def increment_views_background(
            self,
            *,
            post_id: int
    ) -> None:
        """
        [Background Task] Redis에 저장된 조회수를 증가시키고, 일정 주기로 DB에 동기화
        """
        cache_key = f"post:views:{post_id}"
        new_views = await self.redis.incr(cache_key)
        if new_views % 10 == 0: 
            async with UnitOfWork(self.session_factory) as uow:
                await uow.posts.sync_views(post_id=post_id, views=new_views)
            
    async def read_post_list(
        self,
        uow: UnitOfWork,
        *,
        category: PostCategory | None,
        search_title: str | None,
        search_content: str | None,
        author: str | None,
        offset: int,
        limit: int,
    ) -> list[PostSummary]:
        """
        검색 조건에 맞는 게시글 목록 조회
        """
        async with uow:
            posts = await uow.posts.get_posts_list(
                category=category,
                search_title=search_title,
                search_content=search_content,
                author=author,
                offset=offset,
                limit=limit,
            )
            return [PostSummary.model_validate(post) for post in posts]
    
    
    async def create_post(
        self,
        uow: UnitOfWork,
        *,
        user_id: int,
        data: PostCreate,
    ) -> PostSummary:
        """
        새로운 게시글 생성
        """
        async with uow:
            post = await uow.posts.create_post(
                author_id=user_id,
                title=data.title,
                content=data.content,
                category=data.category
            )
            return PostSummary.model_validate(post)

    
    async def toggle_like_post(
        self,
        uow: UnitOfWork,
        *,
        post_id: int,
        user_id: int,
        use_counter_cache: bool = True,
    ) -> tuple[bool, int]:
        """
        게시글에 좋아요를 누르거나 취소 (Toggle)

        Raises:
            PostNotFoundException: 해당 게시글이 존재하지 않는 경우
        """
        async with uow:
            if not await uow.posts.get_post(post_id=post_id):
                raise PostNotFoundException(post_id=post_id)

            exists = await uow.likes.exists_like(
                post_id=post_id,
                user_id=user_id,
            )

            if exists:                
                # like -> unlike
                method = (
                    uow.likes.unlike_with_counter_cache 
                    if use_counter_cache 
                    else uow.likes.unlike_without_counter_cache
                )
                is_liked = False
            else:
                # unlike -> like
                method = (
                    uow.likes.like_with_counter_cache 
                    if use_counter_cache 
                    else uow.likes.like_without_counter_cache
                )
                is_liked = True
                
            _, count = await method(post_id=post_id, user_id=user_id)

            return is_liked, count
        
        
    async def soft_delete_post(
        self,
        uow: UnitOfWork,
        *,
        post_id: int,
        user_id: int,
    ) -> None:
        """
        게시글 삭제 (Soft Delete)

        Raises:
            PostNotFoundException: 게시글이 없거나 이미 삭제된 경우
            UserMismatchException: 작성자 본인이 아닌 경우
            InternalServerException: 예상치 못한 DB 에러 발생 시
        """
        async with uow:
            result = await uow.posts.soft_delete_post_core(
                post_id=post_id, user_id=user_id
            )

        if result.status == RepoStatus.SUCCESS:
            return

        if result.status in (RepoStatus.NOT_FOUND, RepoStatus.ALREADY_DELETED):
            raise PostNotFoundException(post_id=post_id)
        if result.status == RepoStatus.FORBIDDEN:
            raise UserMismatchException()        
        raise InternalServerException()

    
    async def update_post_core(
        self,
        uow: UnitOfWork,
        *,
        post_id: int,
        user_id: int,
        data: PostUpdate,
    ) -> PostDetailCore:
        """
        게시글의 제목, 내용, 카테고리 수정

        Raises:
            PostNotFoundException: 게시글이 없거나 삭제된 경우
            UserMismatchException: 작성자 본인이 아닌 경우
            InternalServerException: 예상치 못한 DB 에러 발생 시
        """
        async with uow:
            result = await uow.posts.update_post_core(
                post_id=post_id,
                user_id=user_id,
                title=data.title,
                content=data.content,
                category=data.category
            )

        if result.status == RepoStatus.SUCCESS:
            return PostDetailCore.model_validate(result.data)

        if result.status == RepoStatus.NOT_FOUND:
            raise PostNotFoundException(post_id=post_id)
        if result.status == RepoStatus.FORBIDDEN:
            raise UserMismatchException()
        raise InternalServerException()

    async def get_comments_for_post(
        self,
        uow: UnitOfWork,
        *,
        post_id: int,
        limit: int = 100,
        offset: int = 0,
    ) -> list[CommentPublic]:
        """
        특정 게시글에 달린 댓글 목록 조회

        Raises:
            PostNotFoundException: 게시글이 존재하지 않는 경우
        """
        async with uow:
            if not await uow.posts.exists(post_id=post_id):
                raise PostNotFoundException(post_id=post_id)

            comments = await uow.comments.get_comments(
                post_id=post_id,
                limit=limit,
                offset=offset
            )
            return [CommentPublic.model_validate(comment) for comment in comments]

    async def toggle_bookmark_to_post(
        self,
        uow: UnitOfWork,
        *,
        post_id: int,
        user_id: int,        
    ) -> None:
        """
        게시글을 북마크에 추가하거나 제거 (Toggle)

        Raises:
            PostNotFoundException: 게시글이 존재하지 않는 경우
        """
        async with uow:
            if not await uow.posts.exists(post_id=post_id):
                raise PostNotFoundException(post_id=post_id)
            
            exists = await uow.bookmarks.exists(
                post_id=post_id,
                user_id=user_id,
            )
            
            if exists:
                await uow.bookmarks.remove(
                    post_id=post_id,
                    user_id=user_id,
                )
            else:
                await uow.bookmarks.regist(
                    post_id=post_id,
                    user_id=user_id,
                )