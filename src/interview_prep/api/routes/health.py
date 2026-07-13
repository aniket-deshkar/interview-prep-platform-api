from fastapi import APIRouter, Response, status
from redis.asyncio import Redis
from sqlalchemy import text

from interview_prep.api.dependencies import SessionDep
from interview_prep.core.config import get_settings

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live", summary="Process liveness")
async def liveness() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/ready", summary="Dependency readiness")
async def readiness(session: SessionDep, response: Response) -> dict[str, object]:
    checks: dict[str, str] = {}
    try:
        await session.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception:
        checks["postgres"] = "unavailable"

    redis = Redis.from_url(get_settings().redis_url)
    try:
        await redis.ping()
        checks["redis"] = "ok"
    except Exception:
        checks["redis"] = "unavailable"
    finally:
        await redis.aclose()

    healthy = all(value == "ok" for value in checks.values())
    if not healthy:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "ok" if healthy else "degraded", "checks": checks}
