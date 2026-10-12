import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
import asyncio

from sqlalchemy import select

from app.core.enums import TableStatus
from app.db.session import SessionLocal
from app.models.restaurant import Branch, Restaurant, Table, Zone


async def seed_restaurant() -> None:
    async with SessionLocal() as session:
        restaurant = await session.scalar(
            select(Restaurant).limit(1)
        )

        if not restaurant:
            restaurant = Restaurant(
                name="Restaurante Imperial",
                legal_name="Restaurante Imperial",
                address="Lorica, Córdoba, Colombia",
                phone="",
                email="admin@imperial.local",
                currency="COP",
                timezone="America/Bogota",
                default_tax_rate="0.08",
                default_tip_rate="0.10",
                is_active=True,
            )
            session.add(restaurant)
            await session.flush()
            print("Restaurante creado.")

        branch = await session.scalar(
            select(Branch).where(
                Branch.restaurant_id == restaurant.id
            )
        )

        if not branch:
            branch = Branch(
                restaurant_id=restaurant.id,
                name="Sede Principal",
                address=restaurant.address,
                phone=restaurant.phone,
                is_active=True,
            )
            session.add(branch)
            await session.flush()
            print("Sucursal principal creada.")

        zone = await session.scalar(
            select(Zone).where(
                Zone.branch_id == branch.id,
                Zone.name == "Salón",
            )
        )

        if not zone:
            zone = Zone(
                branch_id=branch.id,
                name="Salón",
                description="Zona principal de mesas del restaurante",
                is_active=True,
            )
            session.add(zone)
            await session.flush()
            print("Zona Salón creada.")

        for table_number in range(1, 11):
            existing_table = await session.scalar(
                select(Table).where(
                    Table.branch_id == branch.id,
                    Table.number == table_number,
                )
            )

            if not existing_table:
                table = Table(
                    branch_id=branch.id,
                    zone_id=zone.id,
                    number=table_number,
                    capacity=4,
                    status=TableStatus.LIBRE,
                    is_active=True,
                )
                session.add(table)
                print(f"Mesa {table_number} creada.")

        await session.commit()
        print("Seed de restaurante, sucursal, zonas y mesas completado.")


if __name__ == "__main__":
    asyncio.run(seed_restaurant())
