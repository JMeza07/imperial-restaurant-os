from redis.asyncio import Redis

from app.core.config import settings


redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=True)


def _login_key(email: str) -> str:
    return f"auth:login:fail:{email.strip().lower()}"


def _revoked_key(jti: str) -> str:
    return f"auth:revoked:{jti}"


async def set_token_revoked(jti: str, expires_in: int) -> None:
    if expires_in <= 0:
        expires_in = 1

    await redis_client.setex(_revoked_key(jti), expires_in, "1")


async def is_token_revoked(jti: str) -> bool:
    return bool(await redis_client.exists(_revoked_key(jti)))


async def get_login_failures(email: str) -> int:
    value = await redis_client.get(_login_key(email))
    return int(value) if value else 0


async def register_login_failure(email: str) -> None:
    key = _login_key(email)
    ttl = settings.LOGIN_BLOCK_MINUTES * 60

    pipe = redis_client.pipeline()
    pipe.incr(key)
    pipe.expire(key, ttl)
    await pipe.execute()


async def reset_login_failures(email: str) -> None:
    await redis_client.delete(_login_key(email))


async def is_login_blocked(email: str) -> bool:
    failures = await get_login_failures(email)
    return failures >= settings.LOGIN_MAX_FAILURES
