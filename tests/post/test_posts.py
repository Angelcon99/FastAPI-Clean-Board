import asyncio
import pytest
from httpx import AsyncClient, Response
from sqlalchemy import select

from app.core.enums import PostCategory
from app.models.post import Post


@pytest.mark.asyncio
async def test_create_post(
        authorized_client: AsyncClient
):
    payload = {
        "title": "글작성 테스트",
        "content": "글작성",
        "category": PostCategory.GENERAL
    }    
    response = await authorized_client.post("/v1/posts/", json=payload)
    assert response.status_code == 201
    
    data = response.json()    
    assert data["id"] > 0    
    assert data["title"] == payload["title"]
    assert data["category"] == payload["category"]    
    assert "author" in data
    assert "views" in data    

@pytest.mark.asyncio
async def test_read_post_and_views(
        authorized_client: AsyncClient,
        db_session
):
    payload = {
        "title": "조회수 테스트",
        "content": "조회수",
        "category": PostCategory.GENERAL
    }    
    response1 = await authorized_client.post("/v1/posts/", json=payload)
    assert response1.status_code == 201
    
    post_id = response1.json()["id"]

    # 최초 조회
    response1 = await authorized_client.get(f"/v1/posts/{post_id}")
    assert response1.status_code == 200
    
    data1 = response1.json()    
    views1 = data1["views"]

    # BackgroundTask가 실행될 시간 대기
    await asyncio.sleep(0.5)
    
    # 다시 조회 -> views 증가 확인
    response2 = await authorized_client.get(f"/v1/posts/{post_id}")
    assert response2.status_code == 200
    
    data2 = response2.json()
    views2 = data2["views"]
    assert views2 > views1
    
    query = select(Post).where(Post.id == post_id)
    result = await db_session.execute(query)
    post_db = result.scalar_one_or_none()
        
    assert post_db.views == views1 
    assert post_db.views < views2
    
@pytest.mark.asyncio
async def test_like_unlike_flow(
        authorized_client: AsyncClient
):
    payload = {
        "title": "좋아요 테스트",
        "content": "좋아요",
        "category": PostCategory.GENERAL
    }    
    response = await authorized_client.post("/v1/posts/", json=payload)
    assert response.status_code == 201
    
    post_id = response.json()["id"]

    # 좋아요
    like = await authorized_client.put(f"/v1/posts/{post_id}/like")
    assert like.status_code == 200
    
    like_data = like.json()
    assert "liked" in like_data and like_data["liked"] is True
    assert "likes_count" in like_data and like_data["likes_count"] >= 1    

    # 좋아요 취소
    unlike = await authorized_client.put(f"/v1/posts/{post_id}/like")
    assert unlike.status_code == 200
    
    unlike_data = unlike.json()
    assert "liked" in unlike_data and unlike_data["liked"] is False
    assert "likes_count" in unlike_data and unlike_data["likes_count"] <= 0
    
    # 재조회 후 좋아요 수 확인
    post = await authorized_client.get(f"/v1/posts/{post_id}")
    assert post.status_code == 200
    
    post_data = post.json()
    assert "likes_count" in post_data and post_data["likes_count"] <= 0

@pytest.mark.asyncio
async def test_update_post(
        authorized_client: AsyncClient,
        test_post_id
):
    payload = {
        "title": "수정 테스트",
        "content": "수정 후",
        "category": PostCategory.EVENT
    }
    response = await authorized_client.patch(f"/v1/posts/{test_post_id}", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["title"] == payload["title"]
    assert data["content"] == payload["content"]
    assert data["category"] == payload["category"]

@pytest.mark.asyncio
async def test_delete_post(
        authorized_client: AsyncClient,
        test_post_id,
        db_session
):
    response = await authorized_client.delete(f"/v1/posts/{test_post_id}")
    assert response.status_code == 204

    # 조회 시 404 기대
    response = await authorized_client.get(f"/v1/posts/{test_post_id}")
    assert response.status_code == 404
    
    query = select(Post).where(Post.id == test_post_id)
    result = await db_session.execute(query)
    deleted_post = result.scalar_one_or_none()

    assert deleted_post.is_deleted == True

@pytest.mark.asyncio
async def test_bookmark_lifecycle(
        authorized_client: AsyncClient,
        test_post_id
):
    # 북마크 토글 (등록)
    bookmark_res = await authorized_client.post(f"/v1/posts/{test_post_id}/bookmark")
    assert bookmark_res.status_code == 204
    
    # 북마크 등록 검증
    user_bookmarks_res = await authorized_client.get("/v1/users/me/bookmarks")
    assert user_bookmarks_res.status_code == 200
    
    bookmarks = user_bookmarks_res.json()
    bookmarked_ids = [item["id"] for item in bookmarks] 
    assert test_post_id in bookmarked_ids
    
    # 북마크 토글 (해제)
    unbookmark_res = await authorized_client.post(f"/v1/posts/{test_post_id}/bookmark")
    assert unbookmark_res.status_code == 204

    # 북마크 해제 검증
    user_bookmarks_res_after = await authorized_client.get("/v1/users/me/bookmarks")
    bookmarks_after = user_bookmarks_res_after.json()
    
    bookmarked_ids_after = [item["id"] for item in bookmarks_after]
    assert test_post_id not in bookmarked_ids_after

@pytest.mark.asyncio
async def test_update_others_post_forbidden(
        async_client: AsyncClient,
        test_post_id,
        other_authorized_client
):
    payload = {
        "title": "다른 유저의 글",
        "content": "다른 유저가 수정 시도",
        "category": PostCategory.GENERAL
    }
    response = await other_authorized_client.patch(f"/v1/posts/{test_post_id}", json=payload)

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_read_posts_list_pagination(
        authorized_client: AsyncClient,
        create_dummy_posts,
):
    """
    페이징 및 기본 정렬 테스트
    총 게시글: 15개
    """
    response_page_1 = await authorized_client.get("/v1/posts/?limit=10&offset=0")
    assert response_page_1.status_code == 200

    data_page_1 = response_page_1.json()
    assert len(data_page_1) == 10

    # 정렬 확인 (최신순)
    assert data_page_1[0]["title"] == "Hololive 제목 5"

    response_page_2 = await authorized_client.get("/v1/posts/?limit=10&offset=10")
    assert response_page_2.status_code == 200

    data_page_2 = response_page_2.json()
    assert len(data_page_2) == 5

    assert "Python" in data_page_2[0]["title"]


@pytest.mark.asyncio
async def test_read_posts_list_search_and_filter(
        authorized_client: AsyncClient,
        create_dummy_posts,
):
    """
    검색(제목/내용), 카테고리, 작성자 필터링 테스트
    """

    # 제목 검색
    response_title = await authorized_client.get("/v1/posts/?title=Python")
    assert response_title.status_code == 200
    assert len(response_title.json()) == 10

    # 내용 검색
    response_content = await authorized_client.get("/v1/posts/?content=Youtube")
    assert response_content.status_code == 200

    data_content = response_content.json()
    assert len(data_content) == 5
    assert "Hololive" in data_content[0]["title"]

    # 없는 내용 검색
    response_content2 = await authorized_client.get("/v1/posts/?content=Game")
    assert response_content2.status_code == 200

    data_content2 = response_content2.json()
    assert len(data_content2) == 0

    # 카테고리 필터
    response_category = await authorized_client.get(f"/v1/posts/?category={PostCategory.INFORMATION}")
    assert response_category.status_code == 200
    assert len(response_category.json()) == 10

    # 작성자 검색
    response_author = await authorized_client.get("/v1/posts/?author=코로네")
    assert response_author.status_code == 200
    assert len(response_author.json()) == 15