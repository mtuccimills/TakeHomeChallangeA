from pydantic import BaseModel, EmailStr, Field

# Entidade de los modelos de datos a utilizar en el proyecto.
# Consumir fuente de información externa.

class User(BaseModel):
    id: int
    name: str = Field(min_length=1, max_length=50, alias="username")
    email: EmailStr = Field(max_length=120)
    password: str = Field(min_length=8, max_length=20, alias="password_hash")
    postalCode: int | None = Field(default=None, ge=10000,le=999999)

    # Configuración adicional para el modelo, como ejemplos para la documentación de la API.
    model_config = {
        "from_attributes": True,
        "populate_by_name": True, 
        "json_schema_extra":{
            "example": {
                "id": 1,
                "name": "Matias",
                "email": "matias@gmail.com",
                "password": "asdfaseqwwqdwqdsa",
                "postalCode": 38556
            }
        }
    }


