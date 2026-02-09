import pytest
from sqlalchemy import select
from httpx import AsyncClient
from datetime import datetime, timedelta, timezone

from app.core import security
from app.models.user import User
from app.models.refresh_token import RefreshToken

test_user_email = "testuser@test.com"
test_user_pwd = "newuserpwd1234!"

@pytest.mark.asyncio
async def test_register_test_user(
        async_client: AsyncClient,
        db_session
):
    payload={
        "email": test_user_email,
        "password": test_user_pwd,
        "nickname": "테스트신규유저"
    }    
    response = await async_client.post("/v1/auth/register", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == payload["email"]
    assert "password" not in data
    
    query = select(User).where(User.email == payload["email"])
    result = await db_session.execute(query)
    user = result.scalar_one_or_none()
    
    assert user is not None
    assert user.nickname == payload["nickname"]    
    assert user.hashed_password != payload["password"], "비밀번호 암호화 x"    
    assert security.verify_password(payload["password"], user.hashed_password) is True, "비밀번호 암호화 매칭x"

@pytest.mark.asyncio
async def test_register_duplicate_email_and_nickname(
        async_client: AsyncClient,
        registered_test_user
):
    payload={
        "email": registered_test_user["email"],
        "password": test_user_pwd,
        "nickname": "코로네22"
    }
    response = await async_client.post("/v1/auth/register", json=payload)
    assert response.status_code == 409
    
    payload={
        "email": test_user_email,
        "password": test_user_pwd,
        "nickname": registered_test_user["nickname"]
    }
    response = await async_client.post("/v1/auth/register", json=payload)
    assert response.status_code == 409    

@pytest.mark.asyncio
async def test_login(
        async_client: AsyncClient,
        db_session
):
    payload = {
            "email": test_user_email,
            "password": test_user_pwd,
    }
    response = await async_client.post("/v1/auth/login", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_cleans_up_expired_tokens(
        async_client: AsyncClient,
        db_session,
        registered_test_user
):
    user_email = registered_test_user["email"]
    user_pwd = registered_test_user["password"]
    query = select(User).where(User.email == user_email)
    result = await db_session.execute(query)
    user = result.scalar_one()

    now = datetime.now(timezone.utc)

    # 만료된 토큰
    expired_token_str = security.create_refresh_token({"sub": str(user.id)})
    expired_token_hash = security.hash_refresh_token(expired_token_str)

    expired_token = RefreshToken(
        user_id=user.id,
        token=expired_token_hash,
        expires_at=now - timedelta(days=1),
        created_at=now - timedelta(days=7)
    )

    # 아직 유효한 토큰
    valid_token_str = security.create_refresh_token({"sub": str(user.id)})
    valid_token_hash = security.hash_refresh_token(valid_token_str)

    valid_old_token = RefreshToken(
        user_id=user.id,
        token=valid_token_hash,
        expires_at=now + timedelta(days=3),
        created_at=now - timedelta(hours=1)
    )

    db_session.add(expired_token)
    db_session.add(valid_old_token)
    await db_session.commit()

    # 로그인
    payload = {
        "email": user_email,
        "password": user_pwd,
    }
    response = await async_client.post("/v1/auth/login", json=payload)
    assert response.status_code == 200

    # db 검증
    check_query = select(RefreshToken).where(RefreshToken.user_id == user.id)
    check_result = await db_session.execute(check_query)
    tokens = check_result.scalars().all()

    token = [t.token for t in tokens]
    assert expired_token_hash not in token, "만료된 토큰이 삭제되지 않음"
    assert valid_token_hash in token, "유효한 기존 토큰이 삭제됨"
    assert len(tokens) == 2, f"토큰 개수가 맞지 않음 (기대: 2, 실제: {len(tokens)})"


@pytest.mark.asyncio
async def test_login_fail_wrong_password(async_client: AsyncClient):
    payload = {
        "email": "testuser@test.com",
        "password": "wrongpassword"
    }
    response = await async_client.post("/v1/auth/login", json=payload)

    assert response.status_code == 401