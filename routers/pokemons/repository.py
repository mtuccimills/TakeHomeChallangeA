from datetime import datetime

from sqlalchemy import select, func, delete as sql_delete, update as sql_update

from .entity import PokemonCreate, PokemonUpdate, PokemonResponse, PaginatedPokemonResponse
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload #, Session
from auth import hash_password

# Even though we are using all of our models here, it's a good practice to just import whathever is needed excplicitly
from models import Pokemon


from auth import CurrentUser
from config import settings

class PokemonRepository:
    def __init__(self, db:AsyncSession):
        self.db = db

    async def find_all(self,
        skip: int = 0,
        limit: int = settings.max_child_per_page,
    ) -> PaginatedPokemonResponse:
        count_result = await self.db.execute(select(func.count()).select_from(Pokemon))
        total = count_result.scalar_one()

        result = await self.db.execute(
            select(Pokemon)
                .options(selectinload(Pokemon.owner))
                .order_by(Pokemon.date_captured.desc())
                .offset(skip)
                .limit(limit)
                )
        db_Pokemons = result.scalars().all()

        has_more = skip + len(db_Pokemons) < total

        return  PaginatedPokemonResponse(
            pokemons=[PokemonResponse.model_validate(Pokemon) for Pokemon in db_Pokemons],
            total=total,
            skip=skip,
            limit=limit,
            has_more=has_more,
        )
        
    async def find_by_id(self, id: int) -> Pokemon | None:
        result = await self.db.execute(select(Pokemon).where(Pokemon.id == id).options(selectinload(Pokemon.owner)))
        db_Pokemon = result.scalars().first()
        if db_Pokemon:
            return db_Pokemon
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = f"Pokemon with id {id} not found"
        )

    async def create(self, current_user: CurrentUser, pokemon: PokemonCreate) -> Pokemon:
        new_db_Pokemon = Pokemon(
            pokemon_id=pokemon.pokemon_id,
            user_id=current_user.id
        )
        self.db.add(new_db_Pokemon)
        await self.db.commit()
        await self.db.refresh(new_db_Pokemon, attribute_names=["owner"])
        return new_db_Pokemon


    async def update_full(self, pokemon_id: int, current_user: CurrentUser, pokemon_data: PokemonCreate) -> Pokemon:
        db_pokemon = await self.find_by_id(pokemon_id)

        if db_pokemon.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not ownerized to update this pokemon",
            )

        db_pokemon.pokemon_id = pokemon_data.pokemon_id
        await self.db.commit()
        await self.db.refresh(db_pokemon, attribute_names=["owner"])
        return db_pokemon

    async def update_partial(self, pokemon_id: int, current_user: CurrentUser, pokemon_data: PokemonUpdate) -> Pokemon:
        db_pokemon = await self.find_by_id(pokemon_id)

        if db_pokemon.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not ownerized to update this pokemon",
            )

        update_date = pokemon_data.model_dump(exclude_unset=True)
        for field, value in update_date.items():
            setattr(db_pokemon, field, value)
        await self.db.commit()
        await self.db.refresh(db_pokemon, attribute_names=["owner"])
        return db_pokemon

    async def delete(self, id, current_user: CurrentUser) -> bool:

        db_pokemon = await self.find_by_id(id)

        if db_pokemon.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not ownerized to delete this pokemon",
            )

        await self.db.delete(db_pokemon)
        await self.db.commit()
        return True
