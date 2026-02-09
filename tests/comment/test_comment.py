import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.comment import Comment


@pytest.mark.asyncio
async def test_create_comment(authorized_client: AsyncClient, test_post_id):
    payload_first = {
        "post_id": test_post_id,
        "parent_id": None,
        "content": "첫 댓글"
    }
    response_parent = await authorized_client.post("/v1/comments/", json=payload_first)
    assert response_parent.status_code == 201

    data = response_parent.json()
    first_comment_id = data["id"]
    assert data["parent_id"] is None
    assert "user" in data
    assert data["user"]["nickname"] == "코로네"

    payload_second = {
        "post_id": test_post_id,
        "parent_id": first_comment_id,
        "content": "첫 댓글의 대댓글"
    }
    response_child = await authorized_client.post("/v1/comments/", json=payload_second)
    assert response_child.status_code == 201

    child_data = response_child.json()
    assert child_data["parent_id"] == first_comment_id
    assert child_data["content"] == payload_second["content"]

@pytest.mark.asyncio
async def test_update_comment(authorized_client: AsyncClient, test_post_id):
    payload = {
        "post_id": test_post_id,
        "parent_id": None,
        "content": "수정 전 댓글"
    }
    create_res = await authorized_client.post("/v1/comments/", json=payload)
    comment_id = create_res.json()["id"]

    update_payload = {
        "content": "수정된 댓글"
    }
    response = await authorized_client.patch(f"/v1/comments/{comment_id}", json=update_payload)
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == comment_id
    assert data["content"] == update_payload["content"]

@pytest.mark.asyncio
async def test_delete_comment(authorized_client: AsyncClient, test_post_id, db_session):
    payload = {
        "post_id": test_post_id,
        "parent_id": None,
        "content": "삭제될 댓글"
    }
    create_response = await authorized_client.post("/v1/comments/", json=payload)
    comment_id = create_response.json()["id"]

    delete_response = await authorized_client.delete(f"/v1/comments/{comment_id}")
    assert delete_response.status_code == 204

    # db 검증
    query = select(Comment).where(Comment.id == comment_id)
    result = await db_session.execute(query)
    comment_in_db = result.scalar_one_or_none()

    # soft delete
    if comment_in_db:
        assert comment_in_db.is_deleted is True
    # hard delete
    else:
        assert comment_in_db is None


@pytest.mark.asyncio
async def test_reply_depth_limit(authorized_client: AsyncClient, test_post_id):
    parent_payload = {
        "post_id": test_post_id,
        "parent_id": None,
        "content": "댓글"
    }
    parent_response = await authorized_client.post("/v1/comments/", json=parent_payload)
    parent_id = parent_response.json()["id"]

    child_payload = {
        "post_id": test_post_id,
        "parent_id": parent_id,
        "content": "대댓글"
    }
    child_response = await authorized_client.post("/v1/comments/", json=child_payload)
    child_id = child_response.json()["id"]

    payload = {
        "post_id": test_post_id, "parent_id": child_id, "content": "대대댓글"
    }
    response = await authorized_client.post("/v1/comments/", json=payload)

    assert response.status_code == 400