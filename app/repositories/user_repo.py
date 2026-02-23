from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, exists

from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.utils.security import hash_password


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, data: RegisterRequest) -> User:
        user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_by_id(self, user_id: int) -> Optional[User]:
        result = await self.session.scalars(select(User).where(User.id == user_id))
        return result.one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.scalars(select(User).where(User.email == email))
        return result.one_or_none()

    async def exists_by_email(self, email: str) -> bool:
        result = await self.session.execute(select(exists().where(User.email == email)))
        return bool(result.scalar())
