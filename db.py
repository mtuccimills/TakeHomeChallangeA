import os
from urllib.parse import quote_plus
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
#import pyodbc
from dotenv import load_dotenv

load_dotenv()

server = os.getenv("DB_SERVER")
port = os.getenv("DB_PORT")
name = os.getenv("DB_NAME")
username = os.getenv("DB_USER")
password = quote_plus(os.getenv("DB_PASSWORD"))

driver = os.getenv("DB_DRIVER")
# PostgreSQl connection string
DATABASE_URL = (
    f"postgresql+asyncpg://{username}:{password}"
    f"@{server}:{port}/{name}"
)

engine = create_async_engine(DATABASE_URL)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
