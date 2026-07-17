from .entity import PokemonResponse, PokemonCreate, PokemonUpdate, PaginatedPokemonResponse
from .service import PokemonService
from .repository import PokemonRepository
from fastapi import APIRouter, status, Depends, HTTPException, Query
#from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
#from db import get_db
from db import get_db

from auth import CurrentUser

# Pagination
from typing import Annotated
from config import settings

# Maneja JSON Validator, SWAGGER, Auth.
router = APIRouter()

# Iniciamos la vida de la conexión a la base de datos desde que llega la conexión, auqnue no la usemos hasta que lleguemos al controlador.
def get_service(db: AsyncSession = Depends(get_db)) -> PokemonService:
    repository = PokemonRepository(db)
    return PokemonService(repository) # db -> repository -> service

@router.get("/", response_model=PaginatedPokemonResponse)
async def get_pokemons(
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1,le=100)] = settings.max_child_per_page,
    service: PokemonService = Depends(get_service)
    ):
    pokemons = await service.findAll(skip, limit)
    if not pokemons:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No pokemons found"
        )
    return pokemons
@router.get("/{id}", response_model=PokemonResponse)
async def find_by_id(id: int, service: PokemonService = Depends(get_service)):
    return await service.findById(id)

@router.post("/", response_model=PokemonResponse, status_code=status.HTTP_201_CREATED)
async def create_pokemon(pokemon: PokemonCreate, current_user: CurrentUser, service: PokemonService = Depends(get_service)):
    return await service.create(current_user, pokemon)

@router.put("/{id}", response_model=PokemonResponse)
async def update_pokemon(id: int,pokemon: PokemonCreate, current_user: CurrentUser, service: PokemonService = Depends(get_service)):
    return await service.update_full(id, current_user, pokemon)

@router.patch("/{id}", response_model=PokemonResponse)
async def update_pokemon(id: int,pokemon: PokemonUpdate, current_user: CurrentUser, service: PokemonService = Depends(get_service)):
    return await service.update_partial(id, current_user, pokemon)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_pokemon(id: int, current_user: CurrentUser, service: PokemonService = Depends(get_service)):
    return await service.delete(id, current_user)


