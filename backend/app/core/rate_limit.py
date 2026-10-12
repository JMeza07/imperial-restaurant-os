from slowapi import Limiter
from slowapi.util import get_remote_address


limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["500/minute"],
    storage_uri="memory://",
)


def get_limiter() -> Limiter:
    return limiter
