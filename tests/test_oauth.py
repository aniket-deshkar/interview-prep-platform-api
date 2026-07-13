from interview_prep.core.config import Settings
from interview_prep.models.enums import Provider
from interview_prep.services.oauth import build_authorization_request


def test_google_authorization_request_uses_pkce() -> None:
    settings = Settings(google_client_id="client-id")
    request = build_authorization_request(Provider.GOOGLE, settings)
    assert "code_challenge_method=S256" in request.authorization_url
    assert "calendar.readonly" in request.authorization_url
    assert request.state
    assert request.code_verifier
