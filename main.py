from fastapi import FastAPI
from routers.users import controller
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

