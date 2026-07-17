from datetime import datetime 
from pydantic import BaseModel, Field
from routers.users.entity import UserPublic


# Entidade de los modelos de datos a utilizar en el proyecto.
# Consumir fuente de información externa.

from pydantic import BaseModel, ConfigDict, Field

class PokemonBase(BaseModel):
    pokemon_id: int = Field(min=1,max=10000,name="pokemon_id",alias="pokemon_id")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True, 
        "json_schema_extra":{
            "example": {
                "pokemon_id": "1",
            }
        }
    }

class PokemonCreate(PokemonBase):
    pass

class PokemonUpdate(BaseModel):
    pokemon_id: int = Field(min=1,max=10000,name="pokemon_id",alias="pokemon_id")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True, 
        "json_schema_extra":{
            "example": {
                "pokemon_id": "1",
            }
        }
    }


class PokemonResponse(PokemonBase):
    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "pokemon_id": "1",
                "author": "Matias Tucci",
                "date_captured": "2023-01-01",
                "user_id": "10",
            }
        }
    )

    id: int
    user_id:int
    date_captured:datetime
    owner: UserPublic


class PaginatedPokemonResponse(BaseModel):
    pokemons: list[PokemonResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

