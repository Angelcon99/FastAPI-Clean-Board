from sqlalchemy import select
from httpx import AsyncClient
from datetime import datetime, timezone
import pytest

from app.core import security
from app.models.refresh_token import RefreshToken
from app.models.user import User


@pytest.mark.asyncio
async def test_refresh(
        async_client: AsyncClient, 
        db_session, 
        test_user_tokens, 
        test_user_payload
):       
    refresh_token = test_user_tokens["refresh_token"]
    access_token = test_user_tokens["access_token"]
    
    refresh_payload = {
            "refresh_token": refresh_token
    }    
    refresh_response = await async_client.post("v1/auth/refresh", json=refresh_payload)
    assert refresh_response.status_code == 200
    
    refresh_data = refresh_response.json()
    new_access_token = refresh_data["access_token"]
    new_refresh_token = refresh_data["refresh_token"]
    
    assert access_token != new_access_token, "access_token 갱신x"
    assert refresh_token != new_refresh_token, "refresh_token 갱신x"    
    
    user_query = select(User).where(User.email == test_user_payload["email"])
    user_result = await db_session.execute(user_query)
    user = user_result.scalar_one()
    
    token_query = select(RefreshToken).where(RefreshToken.user_id == user.id)
    token_result = await db_session.execute(token_query)
    stored_token_obj = token_result.scalar_one_or_none()
    
    assert stored_token_obj is not None, "DB에 refresh_token 누락"
    is_valid = security.verify_password(new_refresh_token, stored_token_obj.token)
    assert is_valid is True, "새로 발급받은 토큰과 DB에 저장된 해시값 일치x"
        
    assert stored_token_obj.expires_at > datetime.now(timezone.utc), "db에 저장된 토큰 만료 상태"

@pytest.mark.asyncio
async def test_logout(
        authorized_client: AsyncClient,
        test_user_tokens,
        db_session
):
    refresh_token = test_user_tokens["refresh_token"]

    # 로그아웃
    payload = {
        "refresh_token": refresh_token
    }
    response = await authorized_client.post("/v1/auth/logout", json=payload)
    assert response.status_code == 204

    # 로그아웃 후 해당 refresh_token으로 갱신 시도 -> 실패
    refresh_response = await authorized_client.post("/v1/auth/refresh", json=payload)
    assert refresh_response.status_code in [401, 403, 404], "실패 기대"