from datetime import datetime 
from pydantic import BaseModel, Field
from routers.users.entity import UserPublic


# Entidade de los modelos de datos a utilizar en el proyecto.
# Consumir fuente de información externa.

from pydantic import BaseModel, ConfigDict, Field

class PokemonBase(BaseModel):
    name: str = Field(min_length=1, max_length=100,name="name",alias="name")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True, 
        "json_schema_extra":{
            "example": {
                "name": "Pikachu",
            }
        }
    }

class PokemonCreate(PokemonBase):
    pass

class PokemonUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100,name="name")

    model_config = {
        "from_attributes": True,
        "populate_by_name": True, 
        "json_schema_extra":{
            "example": {
                "name": "Pikachu",
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
                "name": "Pikachu",
                "author": "Matias Tucci",
                "date_captured": "2023-01-01",
                "user_id": "10",
            }
        }
    )

    id: int
    user_id:int
    date_captured:datetime
    author: UserPublic


class PaginatedPokemonResponse(BaseModel):
    pokemons: list[PokemonResponse]
    total: int
    skip: int
    limit: int
    has_more: bool

