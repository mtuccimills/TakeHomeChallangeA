from .repository import UserRepository, User
from fastapi import HTTPException, status

class UserService:
    def __init__(self):
        self.repository = UserRepository()

    async def findAll(self):
        return await self.repository.find_all()

    async def findById(self, id):
        return await self.repository.find_by_id(id)

    async def findByEmail(self, email):
        return await self.repository.find_by_email(email)

    async def create(self, user: User):
        user_exist = await self.repository.find_by_email(user.email)
        if user_exist:
            raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="La Persona ya se ha registrado",
        )
        return await self.repository.create(user)

    async def update(self, user: User):
        return await self.repository.update(user)

    async def delete(self, id):
        return await self.repository.delete(id)