from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # , Session

from auth import CurrentUser
from config import settings

# Even though we are using all of our models here, it's a good practice to just import whathever is needed excplicitly
from models import Pokemon

from .entity import PokemonCreate, PokemonUpdate


class PokemonRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_all(
        self, skip: int = 0, limit: int = settings.max_child_per_page
    ) -> tuple[list[Pokemon], int]:
        count_result = await self.db.execute(select(func.count()).select_from(Pokemon))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Pokemon)
            .options(selectinload(Pokemon.owner))
            .order_by(Pokemon.date_captured.desc())
            .offset(skip)
            .limit(limit)
        )
        return list(result.scalars().all()), total

    async def find_by_id(self, id: int) -> Pokemon | None:
        result = await self.db.execute(
            select(Pokemon).where(Pokemon.id == id).options(selectinload(Pokemon.owner))
        )
        db_Pokemon = result.scalars().first()
        return db_Pokemon

    async def create(
        self, current_user: CurrentUser, pokemon: PokemonCreate
    ) -> Pokemon:
        new_db_Pokemon = Pokemon(pokemon_id=pokemon.pokemon_id, user_id=current_user.id)
        self.db.add(new_db_Pokemon)
        await self.db.commit()
        await self.db.refresh(new_db_Pokemon, attribute_names=["owner"])
        return new_db_Pokemon

    async def update_full(
        self, pokemon_id: int, pokemon_data: PokemonCreate
    ) -> Pokemon:
        db_pokemon = await self.find_by_id(pokemon_id)

        db_pokemon.pokemon_id = pokemon_data.pokemon_id
        await self.db.commit()
        await self.db.refresh(db_pokemon, attribute_names=["owner"])
        return db_pokemon

    async def update_partial(
        self, pokemon_id: int, pokemon_data: PokemonUpdate
    ) -> Pokemon:
        db_pokemon = await self.find_by_id(pokemon_id)

        update_date = pokemon_data.model_dump(exclude_unset=True)
        for field, value in update_date.items():
            setattr(db_pokemon, field, value)
        await self.db.commit()
        await self.db.refresh(db_pokemon, attribute_names=["owner"])
        return db_pokemon

    async def delete(self, id) -> bool:

        db_pokemon = await self.find_by_id(id)

        await self.db.delete(db_pokemon)
        await self.db.commit()
        return True
