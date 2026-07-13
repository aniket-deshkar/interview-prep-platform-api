from fastapi import APIRouter, HTTPException, status

from interview_prep.api.dependencies import CurrentUser, SessionDep
from interview_prep.schemas.mock import MockSessionCreate, MockSessionResponse
from interview_prep.services.mock_interviews import create_mock_session

router = APIRouter(prefix="/mock-interviews", tags=["mock interviews"])


@router.post("", response_model=MockSessionResponse, status_code=status.HTTP_201_CREATED)
async def start_mock(
    payload: MockSessionCreate, session: SessionDep, user: CurrentUser
) -> MockSessionResponse:
    try:
        mock = await create_mock_session(session, user.id, payload)
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    return MockSessionResponse.model_validate(mock)
