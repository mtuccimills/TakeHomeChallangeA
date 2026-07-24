from datetime import timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from auth import (
    CurrentUser,
    create_access_token,
    hash_password,
    verify_password,
)
from clients.pokeapi import PokeAPIClient
from config import settings
from routers.pokemons.entity import (
    PokemonForOwner,
    UserPokemonsResponse,
)
from routers.users.entity import UserPublic

from .entity import (
    ChangePasswordRequest,
    Token,
    UserCreate,
    UserPrivate,
    UserPublic,
    UserUpdate,
)
from .repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository, pokeapi_client: PokeAPIClient):
        self.repository = repository
        self.pokeapi_client = pokeapi_client

    async def find_all(self) -> list[UserPublic]:
        users = await self.repository.find_all()
        return [UserPublic.model_validate(user) for user in users]

    async def find_by_id(self, id: int) -> UserPrivate:
        user = await self.repository.find_by_id(id)
        if user:
            return UserPrivate.model_validate(user)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"User with id {id} not found"
        )

    async def find_by_email(self, email: str) -> UserPublic:
        user = await self.repository.find_by_email(email)
        if user:
            return UserPublic.model_validate(user)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with email {email} not found",
        )

    async def find_by_username(self, username: str) -> UserPublic:
        user = await self.repository.find_by_username(username)
        if user:
            return UserPublic.model_validate(user)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with username {username} not found",
        )

    async def change_password(
        self,
        password_data: ChangePasswordRequest,
        current_user: CurrentUser,
    ):
        if not verify_password(
            password_data.current_password, current_user.password_hash
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect",
            )

        new_hash = hash_password(password_data.new_password)

        await self.repository.update_password(current_user.id, new_hash)

        await self.repository.hash_token_delete(current_user.id)

        return {"message": "Password changed successfully"}

    async def create(self, user_data: UserCreate) -> UserPrivate:

        existing_user = await self.repository.find_by_email(user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_data.email} already exists",
            )

        existing_user = await self.repository.find_by_username(user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username {user_data.username} already exists",
            )

        new_user = await self.repository.create(user_data)
        return UserPrivate.model_validate(new_user)

    async def update_full(
        self, user_id: int, current_user: CurrentUser, user_data: UserCreate
    ) -> UserPrivate:
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this user",
            )

        existing_user = await self.find_by_id(user_id)
        existing_user = await self.repository.find_by_email(user_data.email)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Email {user_data.email} not available",
            )
        existing_user = await self.repository.find_by_username(user_data.username)
        if existing_user and existing_user.id != user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Username {user_data.username} not available",
            )

        update_user = await self.repository.update_full(user_id, user_data)
        return UserPrivate.model_validate(update_user)

    async def update_partial(
        self, user_id: int, current_user: CurrentUser, user_data: UserUpdate
    ) -> UserPrivate:
        if user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to update this user",
            )
        if user_data.email:
            existing_user = await self.repository.find_by_email(user_data.email)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Email {user_data.email} not available",
                )

        if user_data.username:
            existing_user = await self.repository.find_by_username(user_data.username)
            if existing_user and existing_user.id != user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Username {user_data.username} not available",
                )

        update_user = await self.repository.update_partial(user_id, user_data)
        return UserPrivate.model_validate(update_user)

    async def delete(self, id: int, current_user: CurrentUser) -> bool:
        if id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not authorized to delete this user",
            )
        user = await self.repository.find_by_id(id)
        if user:
            # old_filename = user.image_file

            result = await self.repository.delete(user.id)

            # if old_filename:
            #     await delete_profile_image(old_filename)

            return result
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id {id} not found",
        )

    async def get_pokemons(
        self, id: int, skip: int, limit: int
    ) -> UserPokemonsResponse:
        user = await self.repository.find_by_id(id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with id {id} not found",
            )

        total = len(user.pokemons)
        page = user.pokemons[skip : skip + limit]  # slice the eager-loaded relationship

        names = await self.pokeapi_client.get_names([p.pokemon_id for p in page])

        pokemons = []
        for p in page:
            dto = PokemonForOwner.model_validate(p)
            dto.name = names.get(p.pokemon_id)
            pokemons.append(dto)

        return UserPokemonsResponse(
            user=UserPublic.model_validate(user),
            pokemons=pokemons,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + len(page) < total,
        )

    # Token function
    async def login_for_access_token(
        self, form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
    ):
        # Look up user by email (case-insensitive)
        # Note: OAuth2PasswordRequestForm uses "username" field, but we treat it as email
        user = await self.repository.find_by_email(form_data.username)

        # Verify user exists and password is correct
        # Don't reveal which one failed (security best practice)
        if not user or not verify_password(form_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Create access token with user id as subject
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            data={"sub": str(user.id)},
            expires_delta=access_token_expires,
        )
        return Token(access_token=access_token, token_type="bearer")
