from fastapi import APIRouter, HTTPException, status
from redis.asyncio import Redis

from interview_prep.api.dependencies import CurrentUser, SettingsDep
from interview_prep.models.enums import Provider
from interview_prep.services.oauth import build_authorization_request

router = APIRouter(prefix="/integrations", tags=["integrations"])


@router.post("/{provider}/authorize")
async def authorize_provider(
    provider: Provider, user: CurrentUser, settings: SettingsDep
) -> dict[str, str]:
    client_id = (
        settings.google_client_id if provider is Provider.GOOGLE else settings.microsoft_client_id
    )
    if not client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"{provider.value.title()} OAuth is not configured",
        )
    request = build_authorization_request(provider, settings)
    redis = Redis.from_url(settings.redis_url)
    try:
        await redis.hset(
            f"oauth-state:{request.state}",
            mapping={
                "user_id": str(user.id),
                "provider": provider.value,
                "code_verifier": request.code_verifier,
            },
        )
        await redis.expire(f"oauth-state:{request.state}", 600)
    finally:
        await redis.aclose()
    return {
        "authorization_url": request.authorization_url,
        "state": request.state,
    }
