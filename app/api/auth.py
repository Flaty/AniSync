from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordBearer

from app.dependencies import CurrentUser, UserRepoDepends, RedisDependency
from app.schemas.auth import RegisterRequest, LoginRequest, TokenResponse, RefreshRequest
from app.services.auth_service import AuthService

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


@router.post('/register', response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    user_repo: UserRepoDepends,
    redis: RedisDependency,
):
    service = AuthService(user_repo=user_repo, redis=redis)
    return await service.register(data)


@router.post('/login', response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    data: LoginRequest,
    user_repo: UserRepoDepends,
    redis: RedisDependency,
):
    service = AuthService(user_repo=user_repo, redis=redis)
    return await service.login(data)


@router.post('/logout', status_code=status.HTTP_200_OK)
async def logout(
    current_user: CurrentUser,
    user_repo: UserRepoDepends,
    redis: RedisDependency,
    token: str = Depends(oauth2_scheme),
):
    service = AuthService(user_repo=user_repo, redis=redis)
    await service.logout(access_token=token, user_id=current_user.id)
    return {"message": "logged out"}


@router.post('/refresh', response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh(
    data: RefreshRequest,
    user_repo: UserRepoDepends,
    redis: RedisDependency,
):
    service = AuthService(user_repo=user_repo, redis=redis)
    return await service.refresh(data.refresh_token)
