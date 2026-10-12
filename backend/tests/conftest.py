import os

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://imperial:change_me@localhost:5432/imperial_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("JWT_SECRET", "test-secret-key-at-least-256-bits")
