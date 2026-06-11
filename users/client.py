from .entity import User
from db import AsyncSessionLocal

# Conexion a la fuente de datos externa, http u ORM, etc.
class UserClient:
    def get_session(self):
        return AsyncSessionLocal()
#Ligero cambio
