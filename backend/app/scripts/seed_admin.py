import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import asyncio
import os

from sqlalchemy import select

from app.core.enums import UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


async def seed_admin() -> None:
    email = os.getenv("SEED_ADMIN_EMAIL", "admin@imperial.local").strip().lower()
    password = os.getenv("SEED_ADMIN_PASSWORD", "ChangeMe123!")

    async with SessionLocal() as session:
        existing_user = await session.scalar(
            select(User).where(User.email == email)
        )

        if existing_user:
            print(f"Ya existe un usuario administrador con el correo {email}.")
            return

        admin_user = User(
            email=email,
            full_name="Administrador Imperial",
            hashed_password=hash_password(password),
            role=UserRole.ADMIN,
            is_active=True,
            mfa_enabled=False,
        )

        session.add(admin_user)
        await session.commit()

        print(f"Usuario administrador creado: {email}")


if __name__ == "__main__":
    asyncio.run(seed_admin())
