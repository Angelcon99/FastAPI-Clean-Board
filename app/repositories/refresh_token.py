from typing import Sequence

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from datetime import datetime, timezone

from app.models.refresh_token import RefreshToken


class RefreshTokenRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def get_token(
            self,
            token: str
    ) -> RefreshToken | None:
        stmt = select(RefreshToken).where(RefreshToken.token == token)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_all_tokens_by_user(
            self,
            user_id: int
    ) -> Sequence[RefreshToken]:
        stmt = select(RefreshToken).where(RefreshToken.user_id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    # ----------------------------------------------------------------
    # Create / Update Operations
    # ----------------------------------------------------------------
    async def create_token(
        self,
        *,
        user_id: int,
        token: str,
        expires_at: datetime,
    ) -> RefreshToken:
        """
        새로운 Refresh token 발급
        """
        db_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(db_token)        
        await self.db.flush()
        return db_token

    # ----------------------------------------------------------------
    # Delete Operations
    # ----------------------------------------------------------------
    async def delete_all_token_by_user(
        self, 
        user_id: int
    ) -> None:
        """
        모든 Refresh token 삭제
        """
        stmt = delete(RefreshToken).where(RefreshToken.user_id == user_id)
        await self.db.execute(stmt)

    async def delete_expired_tokens(
        self,
        user_id: int
    ) -> None:
        """
        만료된 Refresh token 삭제
        """
        stmt = delete(RefreshToken).where(
            RefreshToken.user_id == user_id,
            RefreshToken.expires_at < datetime.now(timezone.utc)
        )
        await  self.db.execute(stmt)