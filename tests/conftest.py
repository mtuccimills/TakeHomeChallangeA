
import os
from collections.abc import AsyncGenerator


# Base de datos de pruebas, se mantiene el mismo usario  y base de datos que producción
# debido a que es el que se genera con docker-compose, pero debería de ser diferente
os.environ["DATABASE_URL"] = (
#    "postgresql+psycopg://userdb_test:password_test@localhost:5432/test_userdb"
    "postgresql+psycopg://userdb:password@localhost:5432/userdb"
)
# os.environ["S3_BUCKET_NAME"] = "test-bucket"
# os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"

# os.environ["S3_ACCESS_KEY_ID"] = "testing"
# os.environ["S3_SECRET_ACCESS_KEY"] = "testing"
# os.environ["S3_REGION"] = "us-east-1"

# # For boto3, the client searches for this variables.
# os.environ["AWS_ACCESS_KEY_ID"] = "testing"
# os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
# os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

# The import order matters, the os variables have to be initialized before adding the db and the app
# import boto3
# from moto import mock_aws
import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import sys
import asyncio

from db import Base, get_db
from main import app



@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

pytest_plugins = ["anyio"]

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(scope="session")
def test_engine():
    engine = create_async_engine(
        os.environ["DATABASE_URL"],
        poolclass=NullPool, # Can cause issues between test like connection already closed and so on
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

@pytest.fixture # Function scope, which is the default, running for each function
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
        join_transaction_mode="create_savepoint", # This is the fake commit magic
    )

    async with test_async_session() as session:
        try:
            yield session
        finally:
            await session.close()
            await trans.rollback()
            await conn.close()


# S3, using moto3 instead of uploading to S3
# @pytest.fixture
# def mocked_aws():
#     with mock_aws():
#         s3 = boto3.client("s3", region_name="us-east-1")
#         s3.create_bucket(Bucket=os.environ["S3_BUCKET_NAME"])
#         yield s3

# Client, with dependencies override
@pytest.fixture
async def client(
    db_session: AsyncSession,
    mocked_aws,
) -> AsyncGenerator[AsyncClient]:

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(
        transport=ASGITransport(app=app), # This is what makes the call of the different http request
        base_url="http://test", # It doesn't matter which url is used, just to have one
    ) as ac:
        yield ac

    app.dependency_overrides.clear()

    # startup  code won't apply here, use the ASGI lifespan, which is outside of the scope.


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

#10:49:52
# Our test will not touch production or development database.
# We are going to create a separate postgres database. 
# Not using sqllite because it's begaviour is different.

