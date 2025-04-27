from fastapi import Request, HTTPException
import redis.asyncio as redis

# --- Dependency Provider for Redis --- #
async def get_redis(request: Request) -> redis.Redis:
    """Dependency to get a Redis connection from the pool stored in app.state."""
    if not hasattr(request.app.state, 'redis_pool') or not request.app.state.redis_pool:
        raise HTTPException(status_code=503, detail="Redis connection pool not available.")
    # Return a Redis client instance using the pool
    return redis.Redis(connection_pool=request.app.state.redis_pool)
# -------------------------------------- # 