import asyncio
import sys
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from fakeredis import aioredis

from app.core.enums import PostCategory
from app.db.base import Base
from app.api.dependency import get_post_service, get_uow
from app.core.uow import UnitOfWork
from app.services.post_service import PostService


# 테스트 DB URL
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:5ohs0267@localhost:5432/board_fastapi_test"

if sys.platform.startswith("win"):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


# ================================================================
# Infrastructure Fixtures (DB, Redis)
# ================================================================
@pytest_asyncio.fixture(scope="session")
async def test_redis_client():
    client = aioredis.FakeRedis(decode_responses=True)
    yield client
    await client.aclose()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def prepare_database(async_engine):
    """테스트 세션 시작 전 DB 스키마 초기화"""
    async with async_engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres;"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public;"))
        await conn.run_sync(Base.metadata.create_all)
    yield


@pytest.fixture(scope="session")
def session_factory(async_engine):
    return sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
        autocommit=False,
    )


# ================================================================
# App & Dependency Overrides
# ================================================================
@pytest.fixture(scope="session")
def app_instance():
    from app.main import app
    app.state.testing = True
    return app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def override_dependencies(session_factory, app_instance, test_redis_client):
    """UnitOfWork와 Redis 의존성을 테스트용으로 교체"""

    async def override_get_uow():
        async with UnitOfWork(session_factory) as uow:
            yield uow

    def override_get_post_service():
        return PostService(
            session_factory=session_factory,
            redis_client=test_redis_client
        )

    app_instance.dependency_overrides[get_uow] = override_get_uow
    app_instance.dependency_overrides[get_post_service] = override_get_post_service

    yield
    app_instance.dependency_overrides.clear()


# ================================================================
# Client & Session
# ================================================================
@pytest_asyncio.fixture(scope="session")
async def async_client(app_instance):
    """비로그인 상태의 기본 클라이언트"""
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest_asyncio.fixture
async def db_session(session_factory):
    async with session_factory() as session:
        yield session


# ================================================================
# Test Data Fixtures (User, Auth, Posts)
# ================================================================
@pytest.fixture(scope="session")
def test_user_payload():
    return {
        "email": "korone@test.com",
        "password": "testpassword1234!",
        "nickname": "코로네"
    }


@pytest_asyncio.fixture(scope="session")
async def registered_test_user(async_client: AsyncClient, test_user_payload):
    response = await async_client.post("/v1/auth/register", json=test_user_payload)
    assert response.status_code in [201, 409]
    return test_user_payload


@pytest_asyncio.fixture(scope="session")
async def test_user_tokens(async_client: AsyncClient, registered_test_user):
    payload = {
        "email": registered_test_user["email"],
        "password": registered_test_user["password"]
    }
    response = await async_client.post("/v1/auth/login", json=payload)
    assert response.status_code == 200
    return response.json()


@pytest_asyncio.fixture(scope="session")
async def authorized_client(async_client: AsyncClient, test_user_tokens):
    """로그인된 상태의 클라이언트"""
    access_token = test_user_tokens["access_token"]
    async_client.headers.update({"Authorization": f"Bearer {access_token}"})
    return async_client


@pytest.fixture
async def test_post_id(authorized_client: AsyncClient):
    payload = {"title": "테스트용", "content": "test", "category": PostCategory.GENERAL}
    response = await authorized_client.post("/v1/posts/", json=payload)
    assert response.status_code == 201
    return response.json()["id"]


@pytest_asyncio.fixture
async def create_dummy_posts(authorized_client: AsyncClient, db_session):
    """페이징/검색 테스트용 더미 데이터 생성 (기존 데이터 초기화)"""
    # 데이터 초기화
    await db_session.execute(text("DELETE FROM bookmarks"))
    await db_session.execute(text("DELETE FROM likes"))
    await db_session.execute(text("DELETE FROM comments"))
    await db_session.execute(text("DELETE FROM posts"))
    await db_session.commit()

    # 데이터 생성
    for i in range(1, 11):
        await authorized_client.post("/v1/posts/", json={
            "title": f"Python 제목 {i}",
            "content": f"FastAPI 내용 {i}",
            "category": PostCategory.INFORMATION
        })

    for i in range(1, 6):
        await authorized_client.post("/v1/posts/", json={
            "title": f"Hololive 제목 {i}",
            "content": f"Youtube 내용 {i}",
            "category": PostCategory.GENERAL
        })
    return 15


@pytest_asyncio.fixture(scope="function")
async def other_authorized_client(app_instance):
    """
    다른 유저(제3자)로 로그인한 클라이언트 픽스처
    """
    transport = ASGITransport(app=app_instance)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        other_payload = {
            "email": "other@test.com",
            "password": "otherpassword123!",
            "nickname": "제3자"
        }

        await client.post("/v1/auth/register", json=other_payload)

        payload = {
            "email": other_payload["email"],
            "password": other_payload["password"]
        }
        response = await client.post("/v1/auth/login", json=payload)

        token = response.json()["access_token"]
        client.headers.update({"Authorization": f"Bearer {token}"})

        yield client