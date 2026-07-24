# Pagination
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

# from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession

from auth import CurrentUser
from clients.pokeapi import PokeAPIClient
from config import settings

# from db import get_db
from db import get_db

from .entity import (
    PaginatedPokemonResponse,
    PokemonCreate,
    PokemonResponse,
    PokemonUpdate,
)
from .repository import PokemonRepository
from .service import PokemonService

# Maneja JSON Validator, SWAGGER, Auth.
router = APIRouter()


# Conseguimos dependencia externa
def get_pokeapi_client(request: Request) -> PokeAPIClient:
    return request.app.state.pokeapi_client


# Iniciamos la vida de la conexión a la base de datos desde que llega la conexión, auqnue no la usemos hasta que lleguemos al controlador.
def get_service(
    db: AsyncSession = Depends(get_db),
    pokeapi_client: PokeAPIClient = Depends(get_pokeapi_client),
) -> PokemonService:
    repository = PokemonRepository(db)
    return PokemonService(repository, pokeapi_client)  # db -> repository -> service


@router.get("/", response_model=PaginatedPokemonResponse)
async def get_pokemons(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = settings.max_child_per_page,
    service: PokemonService = Depends(get_service),
):
    pokemons = await service.find_all(skip, limit)
    if not pokemons:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No pokemons found"
        )
    return pokemons


@router.get("/{id}", response_model=PokemonResponse)
async def find_by_id(id: int, service: PokemonService = Depends(get_service)):
    return await service.find_by_id(id)


@router.post("/", response_model=PokemonResponse, status_code=status.HTTP_201_CREATED)
async def create_pokemon(
    pokemon: PokemonCreate,
    current_user: CurrentUser,
    service: PokemonService = Depends(get_service),
):
    return await service.create(current_user, pokemon)


@router.put("/{id}", response_model=PokemonResponse)
async def update_pokemon(
    id: int,
    pokemon: PokemonCreate,
    current_user: CurrentUser,
    service: PokemonService = Depends(get_service),
):
    return await service.update_full(id, current_user, pokemon)


@router.patch("/{id}", response_model=PokemonResponse)
async def update_pokemon(
    id: int,
    pokemon: PokemonUpdate,
    current_user: CurrentUser,
    service: PokemonService = Depends(get_service),
):
    return await service.update_partial(id, current_user, pokemon)


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pokemon(
    id: int, current_user: CurrentUser, service: PokemonService = Depends(get_service)
):
    return await service.delete(id, current_user)
