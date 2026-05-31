# reports/context_processors/cache_helpers.py
"""
Per-user caching helper for context processors.

Usage:
    from reports.context_processors.cache_helpers import cached_context

    @cached_context(ttl=300)
    def my_context_processor(request):
        ...

The result is cached in Redis for `ttl` seconds, keyed by
(function_name, user_id).  This means each user gets their
own cached copy, so role-based filtering stays correct.

To manually invalidate a user's cache (e.g. after data entry):
    from reports.context_processors.cache_helpers import invalidate_user_cache
    invalidate_user_cache(user_id)
"""

from functools import wraps
from django.core.cache import cache

# Default TTL: 5 minutes.  Adjust per processor if needed.
DEFAULT_TTL = 300


def _make_key(func_name: str, user_id: int) -> str:
    return f"ctx_proc:{func_name}:{user_id}"


def cached_context(ttl: int = DEFAULT_TTL):
    """
    Decorator that caches the return value of a context processor
    per authenticated user for `ttl` seconds.
    Unauthenticated requests are never cached.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(request):
            if not request.user.is_authenticated:
                return func(request)

            key = _make_key(func.__name__, request.user.pk)
            cached = cache.get(key)
            if cached is not None:
                return cached

            result = func(request)
            cache.set(key, result, ttl)
            return result

        return wrapper
    return decorator


def invalidate_user_cache(user_id: int):
    """
    Call this after data saves to clear that user's context-processor cache.
    Because we don't know all function names in advance, we use a
    pattern-based delete (works with Redis).
    """
    try:
        from django_redis import get_redis_connection
        conn = get_redis_connection("default")
        # KEY_PREFIX from settings is prepended by Django as "<prefix>:<version>:<key>"
        pattern = f"*ctx_proc:*:{user_id}"
        keys = conn.keys(pattern)
        if keys:
            conn.delete(*keys)
    except (ImportError, Exception):
        # Fallback: clear the whole cache (safe but broader)
        cache.clear()
