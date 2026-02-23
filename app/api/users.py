from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import AnimeRepoDepends, CurrentUser, UserAnimeListRepoDepends
from app.models.user_anime_list import WatchStatus
from app.schemas.user import UserResponse
from app.schemas.user_anime_list import UserAnimeListCreate, UserAnimeListResponse, UserAnimeListUpdate

router = APIRouter()


@router.get('/me', response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return current_user


@router.get('/me/list', response_model=list[UserAnimeListResponse])
async def get_my_list(
    current_user: CurrentUser,
    repo: UserAnimeListRepoDepends,
    status: Optional[WatchStatus] = Query(None),
):
    return await repo.get_by_user(user_id=current_user.id, status=status)


@router.post('/me/list', response_model=UserAnimeListResponse, status_code=status.HTTP_201_CREATED)
async def add_to_list(
    data: UserAnimeListCreate,
    current_user: CurrentUser,
    repo: UserAnimeListRepoDepends,
    anime_repo: AnimeRepoDepends,
):
    if await repo.exists(current_user.id, data.anime_id):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Аниме уже в вашем списке",
        )
    if not await anime_repo.exists_by_id(data.anime_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аниме не найдено в базе данных",
        )
    return await repo.add(user_id=current_user.id, data=data)


@router.patch('/me/list/{anime_id}', response_model=UserAnimeListResponse)
async def update_in_list(
    anime_id: int,
    data: UserAnimeListUpdate,
    current_user: CurrentUser,
    repo: UserAnimeListRepoDepends,
):
    if not data.model_dump(exclude_none=True):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Нет полей для обновления",
        )
    entry = await repo.update(user_id=current_user.id, anime_id=anime_id, data=data)
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аниме не найдено в вашем списке",
        )
    return entry


@router.delete('/me/list/{anime_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_from_list(
    anime_id: int,
    current_user: CurrentUser,
    repo: UserAnimeListRepoDepends,
):
    deleted = await repo.delete(user_id=current_user.id, anime_id=anime_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Аниме не найдено в вашем списке",
        )
