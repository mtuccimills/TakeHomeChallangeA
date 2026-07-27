from contextlib import asynccontextmanager

from fastapi import FastAPI

from clients.pokeapi import PokeAPIClient
from db import engine
from routers.pokemons import controller as controllerPokemon
from routers.users import controller

# -f for specific file name
# --build to ensure rebuild is done every time to get updates
# docker compose -f app.yaml up --build
# --profile test Activates the test profile
# run run one service, one time, one-shot
# --rm test delete the container when it exist, since run stopped it, but didn't deleted it. For cleaningness
# docker compose -f app.yaml --profile test run --rm test

# adding coverals
# uv add --dev coveralls pytest-cov
# uv run pytest --cov=. tests/
# Add token on the circle ci's project->project configuration -> environmental variables

# Part 5
# 36:25 readme
# The readme needs to have
# Title witha  description (mentions how the request should be Content-type:application/json)
# Features with functionalities
# Table for entities
# Author
# # Badges
# Table of contents (for the following parts)
# Technology (used technologies)
# routes
# Pre-requisites
# Run APP (how to run the app)
# Preload Data (how to preload the data, which will be automatic with a script on docker)
# Run tests (How to run the test)
# ## Precommited hooks
# Standars applied
# Deployment

# Do we use precommit hooks?

# 1:26 min


@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.pokeapi_client = PokeAPIClient()
    yield
    # Shutdown
    await app.state.pokeapi_client.close()
    await engine.dispose()


# Aplicación en FastAPI, que incluye el router del controlador de usuarios.
app = FastAPI(lifespan=lifespan)
app.include_router(controller.router, prefix="/api/v1/users", tags=["Users"])
app.include_router(
    controllerPokemon.router, prefix="/api/v1/pokemons", tags=["Pokemons"]
)
