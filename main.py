from fastapi import FastAPI
from routers.users import controller
from routers.pokemons import controller as controllerPokemon
from db import engine
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(_app: FastAPI):
    yield
    # Shutdown
    await engine.dispose()

# Aplicación en FastAPI, que incluye el router del controlador de usuarios.
app = FastAPI(lifespan=lifespan)
app.include_router(controller.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(controllerPokemon.router, prefix="/api/v1/pokemons", tags=["Pokemons"])

