from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import RATE_LIMIT_PER_MINUTE

# Shared Limiter instance. Defined here (not in main.py) so that
# app/api/*.py routers can import and apply it directly to their own
# endpoints with @limiter.limit(...). The app-level default_limits set
# via SlowAPIMiddleware only reliably cover routes defined straight on
# the FastAPI() app (like /health) — routes registered through
# include_router() were found NOT to be covered by that default, so
# sensitive endpoints (login, register, chat, upload) apply the
# decorator explicitly instead of relying on the middleware default.
limiter = Limiter(
    key_func=get_remote_address, default_limits=[f"{RATE_LIMIT_PER_MINUTE}/minute"]
)
