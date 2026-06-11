from .service import UserService, User
from fastapi import APIRouter

# Controlador de usuarios, que funciona como capa de contacto con el exterior. Resuelve Requests y devuelve Responses.
# Maneja JSON Validator, SWAGGER, Auth.
router = APIRouter()
service = UserService()

@router.get("/", response_model=list[User])
async def get_users():
    return await service.findAll()

@router.get("/{id}", response_model=User | None)
async def findById(id: int):
    return await service.findById(int(id))

@router.get("/email/{email}", response_model=User | None)
async def findByEmail(email):
    return await service.findByEmail(email)

@router.post("/", response_model=User | None)
async def create_user(user: User):
    return await service.create(user)

@router.put("/", response_model=User | None)
async def update_user(user: User):
    return await service.update(user)

@router.delete("/{id}", response_model=bool)
async def delete_user(id: int):
    return await service.delete(int(id))


