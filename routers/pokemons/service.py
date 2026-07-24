from fastapi import HTTPException, status

import models
from auth import CurrentUser
from clients.pokeapi import PokeAPIClient
from config import settings

from .entity import (
    PaginatedPokemonResponse,
    PokemonCreate,
    PokemonResponse,
    PokemonUpdate,
)
from .repository import PokemonRepository


class PokemonService:
    def __init__(self, repository: PokemonRepository, pokeapi_client: PokeAPIClient):
        self.repository = repository
        self.pokeapi_client = pokeapi_client

    async def find_all(
        self,
        skip: int = 0,
        limit: int = settings.max_child_per_page,
    ) -> PaginatedPokemonResponse:
        db_pokemons, total = await self.repository.find_all(skip, limit)
        if total == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="No pokemons found"
            )

        # One concurrent batch for the whole page.
        names = await self.pokeapi_client.get_names([p.pokemon_id for p in db_pokemons])

        pokemons = []
        for p in db_pokemons:
            dto = PokemonResponse.model_validate(p)
            dto.name = names.get(p.pokemon_id)
            pokemons.append(dto)

        return PaginatedPokemonResponse(
            pokemons=pokemons,
            total=total,
            skip=skip,
            limit=limit,
            has_more=skip + len(db_pokemons) < total,
        )

    async def find_by_id(self, id: int) -> PokemonResponse:
        pokemon = await self.repository.find_by_id(id)
        if not pokemon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Pokemon with id {id} not found",
            )
        dto = PokemonResponse.model_validate(pokemon)
        dto.name = await self.pokeapi_client.get_name(pokemon.pokemon_id)
        return dto

    async def find_by_id_raw(self, id: int) -> models.Pokemon | None:
        return await self.repository.find_by_id(id)

    async def create(
        self, current_user: CurrentUser, pokemon: PokemonCreate
    ) -> PokemonResponse:
        new_pokemon = await self.repository.create(current_user, pokemon)
        dto = PokemonResponse.model_validate(new_pokemon)
        dto.name = await self.pokeapi_client.get_name(new_pokemon.pokemon_id)
        return dto

    async def update_full(
        self, pokemon_id: int, current_user: CurrentUser, pokemon: PokemonCreate
    ) -> PokemonResponse:
        db_pokemon = await self.repository.find_by_id(pokemon_id)

        if not db_pokemon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pokemon not found",
            )

        if db_pokemon.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner so you can not update this pokemon",
            )

        update_pokemon = await self.repository.update_full(pokemon_id, pokemon)
        dto = PokemonResponse.model_validate(update_pokemon)
        dto.name = await self.pokeapi_client.get_name(update_pokemon.pokemon_id)
        return dto

    async def update_partial(
        self, pokemon_id: int, current_user: CurrentUser, pokemon: PokemonUpdate
    ) -> PokemonResponse:
        db_pokemon = await self.repository.find_by_id(pokemon_id)

        if not db_pokemon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pokemon not found",
            )

        if db_pokemon.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner so you can not update this pokemon",
            )

        update_pokemon = await self.repository.update_partial(pokemon_id, pokemon)
        dto = PokemonResponse.model_validate(update_pokemon)
        dto.name = await self.pokeapi_client.get_name(update_pokemon.pokemon_id)
        return dto

    async def delete(self, id: int, current_user: CurrentUser) -> bool:
        db_pokemon = await self.repository.find_by_id(id)

        if not db_pokemon:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Pokemon not found",
            )

        if db_pokemon.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not the owner so you can not delete this pokemon",
            )

        return await self.repository.delete(id)
