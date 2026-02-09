from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ----------------------------------------------------------------
    # Read Operations
    # ----------------------------------------------------------------
    async def get_by_id(
        self, 
        *, 
        user_id: int
    ) -> Optional[User]:        
        return await self.db.scalar(
            select(User)
            .where(
                User.id == user_id,
                User.is_deleted.is_(False)                
            )
        )
    
    async def get_by_email(
        self,
        *,
        user_email: str
    ) -> Optional[User]:
        return await self.db.scalar(
            select(User)
            .where(
                User.email == user_email,
                User.is_deleted.is_(False)
            )
        )
    
    async def is_available_email(
        self, 
        *, 
        email: str
    ) -> bool:
        """
        이메일 중복 체크
        """
        existing_user = await self.db.scalar(select(User).where(User.email == email))
        return existing_user is None
        
    async def is_available_nickname(
        self,
        *, 
        nickname: str
    ) -> bool:
        """
        닉네임 중복 체크
        """
        existing_user = await self.db.scalar(select(User).where(User.nickname == nickname))
        return existing_user is None

    # ----------------------------------------------------------------
    # Create / Update Operations
    # ----------------------------------------------------------------
    async def register_user(
        self,
        *,        
        email: str,        
        hashed_password: str,
        nickname: str,
    ) -> User:
        user = User(            
            email=email,            
            hashed_password=hashed_password,
            nickname=nickname,
        )
        self.db.add(user)
        await self.db.flush()
        return user