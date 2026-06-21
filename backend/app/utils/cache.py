# Redis cache helper for analysis results.
# Saves Gemini API calls by caching results for 1 hour.
import json
import redis
from app.config import settings
from loguru import logger
 
# Create the Redis connection
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
 
ANALYSIS_TTL = 3600  # Cache analysis results for 1 hour (3600 seconds)
 
 
def cache_key(job_id: str, user_id: str) -> str:
    """Generate a unique cache key for a job+user analysis pair."""
    return f"analysis:{job_id}:{user_id}"
 
 
def get_cached_analysis(job_id: str, user_id: str) -> dict | None:
    """
    Try to get a cached analysis result from Redis.
    Returns the cached dict if found, None if not cached.
    """
    try:
        key = cache_key(job_id, user_id)
        cached = redis_client.get(key)
        if cached:
            logger.debug(f"Cache HIT for job {job_id}")
            return json.loads(cached)
        logger.debug(f"Cache MISS for job {job_id}")
        return None
    except Exception as e:
        # If Redis is down, log and continue — do not crash the analysis
        logger.warning(f"Redis cache get failed: {e}")
        return None
 
 
def set_cached_analysis(job_id: str, user_id: str, data: dict) -> None:
    """
    Store an analysis result in Redis with a 1-hour expiry.
    """
    try:
        key = cache_key(job_id, user_id)
        redis_client.setex(key, ANALYSIS_TTL, json.dumps(data))
        logger.debug(f"Cached analysis for job {job_id} (TTL: {ANALYSIS_TTL}s)")
    except Exception as e:
        logger.warning(f"Redis cache set failed: {e}")
 
 
def invalidate_analysis(job_id: str, user_id: str) -> None:
    """Delete a cached analysis — useful when a job is re-analyzed."""
    try:
        key = cache_key(job_id, user_id)
        redis_client.delete(key)
        logger.debug(f"Invalidated cache for job {job_id}")
    except Exception as e:
        logger.warning(f"Redis cache delete failed: {e}")
