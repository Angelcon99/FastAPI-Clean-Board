import string
from datetime import datetime, timezone, timedelta

from app.core.settings import settings
from app.core.uow import UnitOfWork
from app.exceptions.types import (
    InvalidCredentialsException,
    InvalidTokenException,
    PasswordValidationException,
    RefreshTokenExpiredException,
    RefreshTokenNotFoundException,
    TokenPayloadInvalidException,
    UserExistEmailException,
    UserExistNicknameException,
    UserNotFoundException
)
from app.core import security
from app.schemas.auth_token import TokenResponse
from app.schemas.user import UserRegister, UserResponse
from app.core.security import TokenDecodeException


class AuthService:
    async def authenticate_user(
        self,
        uow: UnitOfWork,
        *,
        token: str,
    ) -> UserResponse:
        """
        액세스 토큰을 검증하고 사용자 정보 반환

        Raises:
            InvalidTokenException: 토큰 서명이 유효하지 않거나 만료된 경우, 또는 payload에서 user_id를 찾을 수 없는 경우
            UserNotFoundException: 토큰은 유효하나, 해당 ID를 가진 사용자가 DB에 존재하지 않는 경우
        """
        user_id = security.extract_user_id_from_token(token)
        if not user_id:
            raise InvalidTokenException()
        
        async with uow:
            user = await uow.users.get_by_id(user_id=user_id)
            if not user:
                raise UserNotFoundException(user_id)

        return UserResponse.model_validate(user)

    async def login(
        self,
        uow: UnitOfWork,
        *,
        email: str,
        password: str,
    ) -> TokenResponse:
        """
        이메일과 비밀번호로 로그인하고 액세스/리프레시 토큰 발급
        로그인 성공 시 기존의 만료된 refresh_token 정리

        Raises:
            InvalidCredentialsException: 이메일이 존재하지 않거나 비밀번호가 일치하지 않는 경우
        """
        async with uow:
            user = await uow.users.get_by_email(user_email=email)
            if not user or not security.verify_password(password, user.hashed_password):
                raise InvalidCredentialsException()

            access_token = security.create_access_token(
                {
                    "sub": str(user.id),
                    "role": user.role
                }
            )
            refresh_token = security.create_refresh_token(
                {
                    "sub": str(user.id)
                }
            )
            
            hashed_refresh_token = security.hash_refresh_token(refresh_token)
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

            await uow.refresh_tokens.delete_expired_tokens(user_id=user.id)
            await uow.refresh_tokens.create_token(
                user_id=user.id, 
                token=hashed_refresh_token,
                expires_at=expires_at
            )                

            return TokenResponse(
                access_token=access_token, 
                refresh_token=refresh_token,
                token_type="bearer"
            )

    async def refresh(
        self,
        uow: UnitOfWork, 
        *, 
        refresh_token: str
    ) -> TokenResponse:
        """
        리프레시 토큰을 사용하여 새로운 액세스/리프레시 토큰 발급
        사용된 리프레시 토큰은 폐기

        Raises:
            InvalidTokenException: 토큰 형식, 타입이 유효하지 않은 경우
            TokenPayloadInvalidException: 토큰 페이로드에 사용자 정보가 없는 경우
            RefreshTokenNotFoundException: 해당 사용자의 리프레시 토큰 기록이 없는 경우
            RefreshTokenExpiredException: 리프레시 토큰의 유효기간이 만료된 경우
            UserNotFoundException: 토큰은 유효하나, 해당 ID를 가진 사용자가 DB에 존재하지 않는 경우
        """
        # 토큰 서명/페이로드 검증
        try:
            payload = security.decode_token(refresh_token)
        except TokenDecodeException:
            raise InvalidTokenException()

        if payload.type != "refresh":
            raise InvalidTokenException("Not a refresh token")

        user_id = int(payload.sub)
        if not user_id:
            raise TokenPayloadInvalidException()
        
        async with uow:
            user_tokens = await uow.refresh_tokens.get_all_tokens_by_user(user_id)
            if not user_tokens:
                raise RefreshTokenNotFoundException()

            matched_token = None
            for stored in user_tokens:
                if security.verify_refresh_token(refresh_token, stored.token):
                    matched_token = stored
                    break

            if not matched_token:
                raise InvalidTokenException()
            
            # refresh_token 만료 체크
            if matched_token.expires_at < datetime.now(timezone.utc):
                await uow.refresh_tokens.delete_all_token_by_user(user_id=user_id)
                raise RefreshTokenExpiredException()

            user = await uow.users.get_by_id(user_id)
            if not user:
                raise UserNotFoundException(user_id)

            await uow.refresh_tokens.delete_all_token_by_user(user_id=user_id)

            new_access_token = security.create_access_token(
                {
                    "sub": str(user_id),
                    "role": user.role
                }
            )
            new_refresh_token = security.create_refresh_token(
                {
                    "sub": str(user_id)
                }
            )
            
            new_hashed_refresh_token = security.hash_refresh_token(new_refresh_token)
            expires_at = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
                        
            await uow.refresh_tokens.create_token(
                user_id=user_id, 
                token=new_hashed_refresh_token,
                expires_at=expires_at
            )

        return TokenResponse(
            access_token=new_access_token, 
            refresh_token=new_refresh_token,
            token_type="bearer"
        )

    async def logout(
        self, 
        uow: UnitOfWork,
        *, 
        refresh_token: str
    ) -> None:
        """
        사용자의 리프레시 토큰을 DB에서 삭제하여 로그아웃 처리

        Raises:
            InvalidTokenException: 토큰 형식, 타입이 유효하지 않은 경우
            TokenPayloadInvalidException: 토큰 페이로드에 사용자 정보가 없는 경우
        """
        try:
            payload = security.decode_token(refresh_token)
        except TokenDecodeException:
             raise InvalidTokenException()

        if payload.type != "refresh":
            raise InvalidTokenException("Not a refresh token")

        user_id = int(payload.sub)
        if not user_id:
            raise TokenPayloadInvalidException()

        async with uow:
            await uow.refresh_tokens.delete_all_token_by_user(user_id=user_id)

    async def register(
        self,
        uow: UnitOfWork, 
        *, 
        data: UserRegister
    ) -> UserResponse:
        """
        새로운 사용자를 등록(회원가입)

        Raises:
            UserExistEmailException: 이미 가입된 이메일인 경우
            UserExistNicknameException: 이미 존재하는 닉네임인 경우
            PasswordValidationException: 비밀번호가 정책을 만족하지 못하는 경우
        """
        # 중복 검사
        async with uow:
            if not await uow.users.is_available_email(email=data.email):
                raise UserExistEmailException(email=data.email)

            if not await uow.users.is_available_nickname(nickname=data.nickname):
                raise UserExistNicknameException(nickname=data.nickname)
        
            self._validate_password_strength(data.password)

            hashed_password = security.hash_password(data.password)

            user = await uow.users.register_user(
                    email=data.email,
                    hashed_password=hashed_password,
                    nickname=data.nickname
                )

        return UserResponse.model_validate(user)

    def _validate_password_strength(
        self,
        password: str
    ) -> None:        
        if not(6 <= len(password) <= 18):
            raise PasswordValidationException("Password must be 6-18 characters long.")
            
        if not any(ch in string.punctuation for ch in password):
            raise PasswordValidationException("Password must include at least one special character.")