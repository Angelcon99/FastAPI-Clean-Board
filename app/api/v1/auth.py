from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependency import (
    get_auth_service, 
    get_uow
)
from app.core.uow import UnitOfWork
from app.schemas.auth_token import LoginRequest, LogoutRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserRegister, UserResponse
from app.services.auth_service import AuthService

router = APIRouter(
    prefix="/v1/auth",
    tags=["Auth"]
)

@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="로그인 (JSON)",
    description="이메일과 비밀번호를 JSON 형식으로 받아 로그인하고, access_token과 refresh_token을 발급합니다."
)
async def login_json(
    data: LoginRequest,
    uow: UnitOfWork = Depends(get_uow),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await svc.login(
        uow, 
        email=data.email,
        password=data.password
    )    

@router.post(
    "/login/form",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="로그인 (Form)",
    description="Swagger UI 등에서 사용하는 OAuth2 Form 데이터(username, password)로 로그인합니다."
)
async def login_form(
    form_data: OAuth2PasswordRequestForm = Depends(),
    uow: UnitOfWork = Depends(get_uow),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await svc.login(
        uow,
        email=form_data.username, 
        password=form_data.password
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="토큰 갱신",
    description="리프레시 토큰을 사용하여 만료된 액세스 토큰을 새로 발급받습니다."
)
async def refresh_token(
    data: RefreshTokenRequest,
    uow: UnitOfWork = Depends(get_uow),
    svc: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    return await svc.refresh(
        uow, 
        refresh_token=data.refresh_token
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="로그아웃",
    description="사용된 리프레시 토큰을 무효화하여 로그아웃합니다."
)
async def logout(
    data: LogoutRequest,
    uow: UnitOfWork = Depends(get_uow),
    svc: AuthService = Depends(get_auth_service),
) -> None:
    await svc.logout(
        uow, 
        refresh_token=data.refresh_token
    )

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="회원가입",
    description="새로운 사용자를 등록합니다. 이메일, 닉네임 중복 체크 등을 수행합니다."
)
async def register(
    data: UserRegister,
    uow: UnitOfWork = Depends(get_uow),
    svc: AuthService = Depends(get_auth_service),
) -> UserResponse:
    user = await svc.register(
        uow, 
        data=data
    )
    
    return user