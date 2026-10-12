from fastapi import APIRouter

from app.api.v1 import (
    auth,
    branches,
    cash,
    catalog,
    commissions,
    delivery,
    details,
    inventory,
    invoices,
    kitchen,
    orders,
    payments,
    reports,
    restaurant,
    system,
    tables,
    turnos,
    users,
    waiter,
    zones,
)

api_router = APIRouter()

# Auth
api_router.include_router(
    auth.router,
    prefix="/auth",
    tags=["auth"],
)

# Users
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
)
api_router.include_router(
    users.admin_router,
    prefix="/admin",
    tags=["admin-users"],
)

# Restaurant, Branches, Zones, Tables
api_router.include_router(
    restaurant.router,
    tags=["restaurant"],
)
api_router.include_router(
    restaurant.admin_router,
    prefix="/admin",
    tags=["admin-restaurant"],
)
api_router.include_router(
    branches.admin_router,
    prefix="/admin",
    tags=["admin-branches"],
)
api_router.include_router(
    zones.admin_router,
    prefix="/admin",
    tags=["admin-zones"],
)
api_router.include_router(
    tables.router,
    tags=["tables"],
)
api_router.include_router(
    tables.admin_router,
    prefix="/admin",
    tags=["admin-tables"],
)

# Catalog (Dishes, Ingredients, Nutrition, Health Benefits)
api_router.include_router(
    catalog.router,
    tags=["catalog"],
)
api_router.include_router(
    catalog.admin_router,
    prefix="/admin",
    tags=["admin-catalog"],
)

# Orders
api_router.include_router(
    orders.router,
    tags=["orders"],
)
api_router.include_router(
    orders.admin_router,
    prefix="/admin",
    tags=["admin-orders"],
)

# Kitchen & Waiter
api_router.include_router(
    kitchen.router,
    tags=["kitchen"],
)
api_router.include_router(
    waiter.router,
    tags=["waiter"],
)
api_router.include_router(
    details.router,
    tags=["details"],
)

# Payments & Cash
api_router.include_router(
    payments.router,
    tags=["payments"],
)
api_router.include_router(
    payments.admin_router,
    prefix="/admin",
    tags=["admin-payments"],
)
api_router.include_router(
    cash.admin_router,
    prefix="/admin",
    tags=["admin-cash"],
)

# Invoices & Facturación
api_router.include_router(
    invoices.router,
    tags=["invoices"],
)
api_router.include_router(
    invoices.admin_router,
    prefix="/admin",
    tags=["admin-invoices"],
)

# Delivery
api_router.include_router(
    delivery.router,
    tags=["delivery"],
)
api_router.include_router(
    delivery.admin_router,
    prefix="/admin",
    tags=["admin-delivery"],
)

# Shifts & Schedules
api_router.include_router(
    turnos.router,
    tags=["turnos"],
)
api_router.include_router(
    turnos.admin_router,
    prefix="/admin",
    tags=["admin-turnos"],
)

# Commissions & Tips
api_router.include_router(
    commissions.router,
    tags=["commissions"],
)
api_router.include_router(
    commissions.admin_router,
    prefix="/admin",
    tags=["admin-commissions"],
)

# Inventory & Suppliers
api_router.include_router(
    inventory.admin_router,
    prefix="/admin",
    tags=["admin-inventory"],
)

# Reports
api_router.include_router(
    reports.admin_router,
    prefix="/admin",
    tags=["admin-reports"],
)

# System Health & Security Hardening
api_router.include_router(
    system.admin_router,
    prefix="/admin",
    tags=["admin-system"],
)
