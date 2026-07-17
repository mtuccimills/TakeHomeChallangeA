from .repository import PokemonRepository
from .entity import PokemonResponse, PokemonCreate, PokemonUpdate, PaginatedPokemonResponse
from auth import CurrentUser
import models
from config import settings

class PokemonService:
    def __init__(self, repository: PokemonRepository):
        self.repository = repository

    async def findAll(
            self,
            skip: int = 0,
            limit: int = settings.max_child_per_page,
) -> PaginatedPokemonResponse:
        return await self.repository.find_all(skip, limit)

    async def find_all_raw(self) -> list[models.Pokemon]:
        return await self.repository.find_all()

    async def findById(self, id: int) -> PokemonResponse:
        pokemon = await self.repository.find_by_id(id)
        return PokemonResponse.model_validate(pokemon)

    async def find_by_id_raw(self, id: int) -> models.Pokemon | None:
        return await self.repository.find_by_id(id)

    async def create(self, current_user: CurrentUser, pokemon: PokemonCreate) -> PokemonResponse:
        new_pokemon = await self.repository.create(current_user, pokemon)
        return PokemonResponse.model_validate(new_pokemon)

    async def update_full(self, pokemon_id: int,current_user: CurrentUser, pokemon: PokemonCreate) -> PokemonResponse:
        update_pokemon = await self.repository.update_full(pokemon_id, current_user, pokemon)
        return PokemonResponse.model_validate(update_pokemon)

    async def update_partial(self, pokemon_id: int, current_user: CurrentUser, pokemon: PokemonUpdate) -> PokemonResponse:
        update_pokemon = await self.repository.update_partial(pokemon_id, current_user, pokemon)
        return PokemonResponse.model_validate(update_pokemon)

    async def delete(self, id: int, current_user: CurrentUser) -> bool:
        return await self.repository.delete(id, current_user)
    
