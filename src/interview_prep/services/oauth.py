import base64
import hashlib
import secrets
from dataclasses import dataclass
from urllib.parse import urlencode

from interview_prep.core.config import Settings
from interview_prep.models.enums import Provider


@dataclass(frozen=True)
class OAuthRequest:
    authorization_url: str
    state: str
    code_verifier: str


PROVIDER_CONFIG = {
    Provider.GOOGLE: {
        "authorize": "https://accounts.google.com/o/oauth2/v2/auth",
        "scopes": [
            "openid",
            "email",
            "https://www.googleapis.com/auth/calendar.readonly",
            "https://www.googleapis.com/auth/gmail.readonly",
        ],
    },
    Provider.MICROSOFT: {
        "authorize": "https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        "scopes": ["openid", "email", "offline_access", "Calendars.Read", "Mail.Read"],
    },
}


def build_authorization_request(provider: Provider, settings: Settings) -> OAuthRequest:
    config = PROVIDER_CONFIG[provider]
    verifier = secrets.token_urlsafe(64)
    challenge = (
        base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    )
    state = secrets.token_urlsafe(32)
    client_id = (
        settings.google_client_id if provider is Provider.GOOGLE else settings.microsoft_client_id
    )
    redirect_uri = f"{settings.oauth_redirect_base_url}/{provider.value}/callback"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(config["scopes"]),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": "offline",
        "prompt": "consent",
    }
    return OAuthRequest(
        authorization_url=f"{config['authorize']}?{urlencode(params)}",
        state=state,
        code_verifier=verifier,
    )
