import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import asyncio
import os

from sqlalchemy import select

from app.core.enums import UserRole
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User


async def get_or_create_user(
    session,
    email: str,
    full_name: str,
    password: str,
    role: UserRole,
) -> None:
    email = email.strip().lower()

    user = await session.scalar(
        select(User).where(User.email == email)
    )

    if user:
        print(f"Usuario ya existe: {email}")
        return

    user = User(
        email=email,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=role,
        is_active=True,
        mfa_enabled=False,
    )

    session.add(user)
    await session.flush()

    print(f"Usuario creado: {email} con rol {role.value}")


async def seed_staff() -> None:
    cocinero_email = os.getenv("SEED_COCINERO_EMAIL", "cocinero@imperial.local")
    cocinero_password = os.getenv("SEED_COCINERO_PASSWORD", "Cocina123!")

    mesero_email = os.getenv("SEED_MESERO_EMAIL", "mesero@imperial.local")
    mesero_password = os.getenv("SEED_MESERO_PASSWORD", "Mesero123!")

    async with SessionLocal() as session:
        await get_or_create_user(
            session=session,
            email=cocinero_email,
            full_name="Cocinero Principal",
            password=cocinero_password,
            role=UserRole.COCINERO,
        )

        await get_or_create_user(
            session=session,
            email=mesero_email,
            full_name="Mesero Principal",
            password=mesero_password,
            role=UserRole.MESERO,
        )

        await session.commit()

    print("Seed de personal completado.")


if __name__ == "__main__":
    asyncio.run(seed_staff())
