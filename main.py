from fastapi import FastAPI
from users.entity import User
from users import controller
from db import Base, engine
from contextlib import asynccontextmanager
import model

@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown
    await engine.dispose()

# Aplicación en FastAPI, que incluye el router del controlador de usuarios.
app = FastAPI(lifespan=lifespan)
app.include_router(controller.router, prefix="/api/v1/users", tags=["Users"])

