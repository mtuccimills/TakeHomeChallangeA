from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from model import User as UserModel
from .client import UserClient, User

class UserRepository:
    def __init__(self):
        self.client = UserClient()

    async def find_all(self) -> list[User]:
        async with self.client.get_session() as session:
            result = await session.execute(select(UserModel))
            return result.scalars().all()

    async def find_by_id(self, id: int) -> UserModel | None:
        async with self.client.get_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == id))
            return result.scalar_one_or_none()

    async def find_by_email(self, email: str) -> UserModel | None:
        async with self.client.get_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.email == email))
            return result.scalar_one_or_none()

    async def create(self, user: User) -> UserModel:
        async with self.client.get_session() as session:
            db_user = UserModel(
                username=user.name,
                email=user.email,
                password_hash=user.password
            )
            session.add(db_user)
            await session.commit()
            await session.refresh(db_user)
            return db_user

    async def update(self, user_data: User) -> UserModel | None:
        async with self.client.get_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == user_data.id))
            db_user = result.scalar_one_or_none()
            if db_user:
                db_user.username = user_data.name
                db_user.email = user_data.email
                db_user.password_hash = user_data.password
                await session.commit()
                await session.refresh(db_user)
            return db_user

    async def delete(self, id: int) -> bool:
        async with self.client.get_session() as session:
            result = await session.execute(select(UserModel).where(UserModel.id == id))
            db_user = result.scalar_one_or_none()
            if db_user:
                await session.delete(db_user)
                await session.commit()
                return True
            return False