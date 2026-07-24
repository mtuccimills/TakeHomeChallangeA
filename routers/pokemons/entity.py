from datetime import datetime

# Entidade de los modelos de datos a utilizar en el proyecto.
# Consumir fuente de información externa.
from pydantic import BaseModel, ConfigDict, Field

from routers.users.entity import UserPublic


class PokemonBase(BaseModel):
    pokemon_id: int = Field(ge=1, le=10000, alias="pokemon_id")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "pokemon_id": "1",
            }
        },
    }


class PokemonCreate(PokemonBase):
    pass


class PokemonUpdate(BaseModel):
    pokemon_id: int = Field(ge=1, le=10000, alias="pokemon_id")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True,
        "json_schema_extra": {
            "example": {
                "pokemon_id": "1",
            }
        },
    }


class PokemonResponse(PokemonBase):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "pokemon_id": "1",
                "name": "bulbasaur",
                "author": "Matias Tucci",
                "date_captured": "2023-01-01",
                "user_id": "10",
            }
        },
    )

    id: int
    user_id: int
    name: str | None = None  # ← filled by the service from PokeAPI
    date_captured: datetime
    owner: UserPublic


class PaginatedPokemonResponse(BaseModel):
    pokemons: list[PokemonResponse]
    total: int
    skip: int
    limit: int
    has_more: bool


class PokemonForOwner(PokemonBase):
    """A captured Pokémon as seen from its owner's perspective — no nested owner."""

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    user_id: int
    date_captured: datetime
    name: str | None = None


class UserPokemonsResponse(BaseModel):
    """One user and their captured Pokémon."""

    user: UserPublic
    pokemons: list[PokemonForOwner]
    total: int
    skip: int
    limit: int
    has_more: bool
