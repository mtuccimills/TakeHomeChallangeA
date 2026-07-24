import os
from collections.abc import AsyncGenerator

# Switch environmental variables to testing (only database here, but it's a good practice)
os.environ.setdefault("APP_ENV", "test")

# The import order matters, the os variables have to be initialized before adding the db and the app
# import boto3
# from moto import mock_aws
import asyncio
import sys
from unittest.mock import AsyncMock

import pytest
from asgi_lifespan import LifespanManager
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from config import settings
from db import Base, get_db
from main import app

pytest_plugins = ["anyio"]


@pytest.fixture(scope="session")
def anyio_backend():
    if sys.platform == "win32":
        return ("asyncio", {"loop_factory": asyncio.SelectorEventLoop})
    return "asyncio"


@pytest.fixture(scope="session")
def test_engine():
    # Print just to valdiate that the change of the database is correctly
    # print(f"\n>>> TEST DB URL: {settings.database_url}\n")
    engine = create_async_engine(
        settings.database_url,  # ← from Settings (which loaded .env.test), not os.environ
        poolclass=NullPool,
    )
    return engine


@pytest.fixture(scope="session")
async def setup_database(test_engine):
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()


@pytest.fixture  # Function scope, which is the default, running for each function
async def db_session(
    test_engine,
    setup_database,
) -> AsyncGenerator[AsyncSession]:
    conn = await test_engine.connect()
    trans = await conn.begin()

    test_async_session = async_sessionmaker(
        bind=conn,
        class_=AsyncSession,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",  # This is the fake commit magic
    )

    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await conn.close()


# Mocking extenral dependencies
@pytest.fixture
def pokeapi_mock():
    mock = AsyncMock()
    mock.get_name.return_value = None
    mock.get_names.return_value = {}
    return mock


# Client, with dependencies override
@pytest.fixture
async def client(db_session: AsyncSession, pokeapi_mock) -> AsyncGenerator[AsyncClient]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with LifespanManager(app):
        # lifespan startup has run → app.state.pokeapi_client is a real PokeAPIClient.
        # Stub only the methods that would hit the network:

        # General mock for the class
        app.state.pokeapi_client = pokeapi_mock

        # Specific mock for class's methods
        # app.state.pokeapi_client.get_name = AsyncMock(return_value=None)
        # app.state.pokeapi_client.get_names = AsyncMock(return_value={})

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac

    app.dependency_overrides.clear()


# Authenthication fixers
async def create_test_user(
    client: AsyncClient,
    username: str = "testuser",
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> dict:
    response = await client.post(
        "/api/v1/users/",
        json={
            "username": username,
            "email": email,
            "password": password,
        },
    )
    assert response.status_code == 201, f"Failed to create user: {response.text}"
    return response.json()


async def login_user(
    client: AsyncClient,
    email: str = "test@example.com",
    password: str = "testpassword123",
) -> str:
    response = await client.post(
        "/api/v1/users/token",
        # OAuth2 expects a form data instead of a json
        data={
            "username": email,
            "password": password,
        },
    )
    assert response.status_code == 200, f"Failed to login: {response.text}"
    return response.json()["access_token"]


def auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


# 10:49:52
# Our test will not touch production or development database.
# We are going to create a separate postgres database.
# Not using sqllite because it's begaviour is different.
