from typing import Annotated

from fastapi.security import OAuth2PasswordRequestForm

from .entity import (
    UserPublic, 
    UserPrivate,
    UserCreate, 
    UserUpdate, 
    Token, 
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ChangePasswordRequest
)
from .service import UserService
from .repository import UserRepository
from routers.pokemon.entity import PaginatedPokemonResponse
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status, UploadFile
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
#from db import get_db
from db import get_db

from auth import CurrentUser

# Pagination
from config import settings
# Controlador de usuarios, que funciona como capa de contacto con el exterior. Resuelve Requests y devuelve Responses.
# Maneja JSON Validator, SWAGGER, Auth.
router = APIRouter()

# We start the connection of the database since the connection is established to the endpoint, even if we use it until we reach the controller.
def get_service(db:AsyncSession = Depends(get_db)) -> UserService:
    repository = UserRepository(db)
    return UserService(repository)

@router.get("/", response_model=list[UserPublic])
async def get_users(service: UserService = Depends(get_service)):
    users = await service.find_all()
    if not users:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No users found"
        )
    return users

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    service: UserService = Depends(get_service),
):
    """Authenticate user and return access token."""
    return await service.login_for_access_token(form_data)

@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    """Get the currently authenticated user."""
    return current_user

@router.patch("/me/password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: ChangePasswordRequest,
    current_user: CurrentUser,
    service: UserService = Depends(get_service),
):
    return await service.change_password(password_data, current_user)

@router.get("/email/{email}", response_model=UserPublic)
async def find_by_email(email: str, service: UserService = Depends(get_service)):
    return await service.find_by_email(email)

@router.get("/username/{username}", response_model=UserPublic)
async def find_by_username(username: str, service: UserService = Depends(get_service)):
    return await service.find_by_username(username)

@router.get("/{user_id}/pokemon", response_model=PaginatedPokemonResponse)
async def get_pokemons(user_id: int,                     
                    skip: Annotated[int, Query(ge=0)] = 0,
                    limit: Annotated[int, Query(ge=1,le=100)] = settings.max_child_per_page,
                    service: UserService = Depends(get_service)):
    return await service.get_pokemons(user_id, skip, limit)

@router.get("/{user_id}", response_model=UserPrivate)
async def find_user_by_id(user_id: int, service: UserService = Depends(get_service)):
    return await service.find_by_id(user_id)

@router.post("/", response_model=UserPrivate, status_code=status.HTTP_201_CREATED)
async def create(user: UserCreate, service: UserService = Depends(get_service)):
    return await service.create(user)

@router.put("/{user_id}", response_model=UserPrivate)
async def update_full(user_id: int, current_user: CurrentUser, user: UserCreate, service: UserService = Depends(get_service)):
    return await service.update_full(user_id,current_user, user)

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_partial(user_id: int, current_user:CurrentUser, user: UserUpdate, service: UserService = Depends(get_service)):
    return await service.update_partial(user_id, current_user, user)

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete(user_id: int, current_user: CurrentUser, service: UserService = Depends(get_service)):
    return await service.delete(user_id, current_user)
