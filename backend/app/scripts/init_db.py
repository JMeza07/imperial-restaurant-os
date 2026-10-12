import asyncio
import os
import sys

# Ensure backend root is in python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from app.db.base import Base
from app.db.session import engine
import app.models  # noqa: F401


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Base de datos inicializada correctamente con todas las tablas.")


if __name__ == "__main__":
    asyncio.run(init_db())
