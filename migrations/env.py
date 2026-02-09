import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool
from sqlalchemy.engine.url import make_url
from alembic import context

from models import user, post, comment, like, refresh_token

# -----------------------------------------------------------
# 0. 프로젝트 루트 path 추가
# -----------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# -----------------------------------------------------------
# 1. 프로젝트 내부 import
# -----------------------------------------------------------
from db.session import DATABASE_URL
from db.base import Base

# Alembic 기본 설정
config = context.config

if config.config_file_name:
    fileConfig(config.config_file_name)

# autogenerate 시 사용할 metadata
target_metadata = Base.metadata

# -----------------------------------------------------------
# 2. async → sync URL 변환
# -----------------------------------------------------------
def make_sync_url(async_url: str):
    url = make_url(async_url)
    if url.drivername.startswith("postgresql+asyncpg"):
        url = url.set(drivername="postgresql+psycopg2")
    return url.render_as_string(hide_password=False)


# -----------------------------------------------------------
# 3. Offline mode
# -----------------------------------------------------------
def run_migrations_offline():
    sync_url = make_sync_url(DATABASE_URL)

    context.configure(
        url=sync_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# -----------------------------------------------------------
# 4. Online mode
# -----------------------------------------------------------
def run_migrations_online():
    sync_url = make_sync_url(DATABASE_URL)

    connectable = create_engine(
        sync_url,
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# -----------------------------------------------------------
# 5. Entry Point
# -----------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
