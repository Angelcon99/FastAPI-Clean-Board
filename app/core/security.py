from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import ExpiredSignatureError, JWTError, jwt
from passlib.context import CryptContext

from app.core.settings import settings
from app.exceptions.types import InvalidTokenException
from app.schemas.auth_token import TokenPayload


pwd_context = CryptContext(
    schemes=["argon2"],
    deprecated="auto"
)

# ----- Password Hashing -----
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# ----- Refresh Token Hashing -----
def hash_refresh_token(token: str) -> str:
    return pwd_context.hash(token)

def verify_refresh_token(token: str, hashed_token: str) -> bool:
    return pwd_context.verify(token, hashed_token)

# ----- JWT 발급 / 파싱 -----
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    to_encode["type"] = "access"

    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    to_encode["type"] = "refresh"

    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

class TokenDecodeException(Exception):
    """토큰 디코딩 중 발생하는 에러"""
    pass

def decode_token(token: str) -> TokenPayload:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return TokenPayload(**payload)
    except (ExpiredSignatureError, JWTError):
        raise TokenDecodeException()

# ----- 인증 -----
def extract_user_id_from_token(token: str) -> int:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise InvalidTokenException()
        return int(user_id)
    except JWTError:
        raise InvalidTokenException()


