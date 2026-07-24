from datetime import datetime

from sqlalchemy import delete as sql_delete
from sqlalchemy import func, select
from sqlalchemy import update as sql_update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # , Session

from auth import hash_password

# Even though we are using all of our models here, it's a good practice to just import whathever is needed excplicitly
from models import PasswordResetToken, Pokemon, User

# from sqlalchemy.ext.asyncio import AsyncSession
# from model import Post
from .entity import UserCreate, UserPrivate, UserUpdate


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(self) -> list[User]:
        result = await self.db.execute(
            select(User).options(selectinload(User.pokemons))
        )
        return result.scalars().all()

    async def find_by_id(self, id: int) -> User | None:
        result = await self.db.execute(
            select(User).where(User.id == id).options(selectinload(User.pokemons))
        )
        return result.scalars().first()

    async def find_by_email(self, email: str) -> User | None:
        result = await self.db.execute(
            select(User).where(User.email == email).options(selectinload(User.pokemons))
        )
        return result.scalars().first()

    async def find_by_username(self, username: str) -> User | None:
        result = await self.db.execute(
            select(User)
            .where(func.lower(User.username) == username.lower())
            .options(selectinload(User.pokemons))
        )
        return result.scalars().first()

    async def create(self, user: UserCreate) -> User:
        db_user = User(
            username=user.username,
            email=user.email.lower(),
            password_hash=hash_password(user.password),
        )

        self.db.add(db_user)
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def update_full(self, user_id: int, user_data: UserPrivate) -> User:
        db_user = await self.find_by_id(user_id)
        db_user.username = user_data.username
        db_user.email = user_data.email.lower()
        await self.db.commit()
        await self.db.refresh(db_user, attribute_names=["pokemons"])
        return db_user

    async def update_partial(self, user_id: int, user_data: UserUpdate) -> User:
        db_user = await self.find_by_id(user_id)

        # Update Logic
        update_data = user_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "email" and value is not None:
                value = value.lower()
            # Password is going to be managed separatly thanks to the tokens and hash; therefore, we will not be updating it here
            if field != "password" and value is not None:
                setattr(db_user, field, value)

        # # Manual update
        # if user_data.username is not None:
        #     db_user.username = user_data.username
        # if user_data.email is not None:
        #     db_user.email = user_data.email.lower()

        await self.db.commit()
        await self.db.refresh(db_user, attribute_names=["pokemons"])
        return db_user

    async def delete(self, id: int) -> bool:
        db_user = await self.find_by_id(id)
        await self.db.delete(db_user)
        await self.db.commit()
        return True

    async def get_pokemons(
        self, id: int, skip: int, limit: int
    ) -> tuple[list[Pokemon], int]:
        result = await self.db.execute(
            select(Pokemon)
            .where(Pokemon.user_id == id)
            .options(selectinload(Pokemon.owner))
            .offset(skip)
            .limit(limit)
        )

        pokemons = result.scalars().all()

        result = await self.db.execute(
            select(func.count()).select_from(Pokemon).where(Pokemon.user_id == id)
            #            select(func.count(Pokemon.id))
            #            .where(Pokemon.user_id == id)
        )

        total = result.scalar() or 0

        return pokemons, total

    # Token related functions
    async def delete_tokens(self, user_id: int):
        await self.db.execute(
            sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )

    async def add_hash_token(self, user_id: int, token_hash: str, expires_at: datetime):
        reset_token = PasswordResetToken(
            user_id=user_id, token_hash=token_hash, expires_at=expires_at
        )
        self.db.add(reset_token)
        await self.db.commit()

    async def hash_token_exists(
        self,
        token_hash: str,
    ) -> PasswordResetToken:
        result = await self.db.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
            )
        )

        return result.scalars().first()

    async def hash_token_expired(
        self,
        token_hash: str,
    ) -> PasswordResetToken:
        reset_token = await self.hash_token_exists(token_hash)
        if reset_token:
            await self.db.delete(reset_token)
            await self.db.commit()

    async def hash_token_delete(
        self,
        user_id: int,
    ) -> PasswordResetToken:
        await self.db.execute(
            sql_delete(PasswordResetToken).where(PasswordResetToken.user_id == user_id)
        )
        await self.db.commit()

    async def update_password(self, user_id: int, password_hash: str) -> None:
        await self.db.execute(
            sql_update(User)
            .where(User.id == user_id)
            .values(password_hash=password_hash)
        )
        await self.db.commit()
