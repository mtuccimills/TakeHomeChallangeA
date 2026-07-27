import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from auth import hash_password
from db import engine
from models import Pokemon, User
import sys


async def seed():
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # --- Idempotency guard: skip if already seeded ---
        existing = await session.execute(select(User).where(User.email == "ash@example.com"))
        if existing.scalar_one_or_none():
            print("Seed data already present — skipping.")
            return

        # --- Users (with hashed passwords so they can log in) ---
        ash = User(
            username="Ash",
            email="ash@example.com",
            password_hash=hash_password("pikachu123"),
        )
        misty = User(
            username="Misty",
            email="misty@example.com",
            password_hash=hash_password("staryu123"),
        )
        session.add_all([ash, misty])
        await session.flush()      # assigns ash.id / misty.id without committing yet

        # --- Pokémon, linked to the users ---
        session.add_all([
            Pokemon(pokemon_id=25, user_id=ash.id),    # Pikachu
            Pokemon(pokemon_id=1, user_id=ash.id),     # Bulbasaur
            Pokemon(pokemon_id=120, user_id=misty.id), # Staryu
            Pokemon(pokemon_id=121, user_id=misty.id), # Starmie
        ])

        await session.commit()
        print("Seeded 2 users and 4 pokemon.")

# Windowd caveat
if __name__ == "__main__":
      if sys.platform == "win32":
          asyncio.run(seed(), loop_factory=asyncio.SelectorEventLoop)  # 3.12+
      else:
          asyncio.run(seed())