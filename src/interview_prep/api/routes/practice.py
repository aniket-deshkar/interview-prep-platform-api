from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from interview_prep.api.dependencies import CurrentUser, SessionDep
from interview_prep.models.entities import PracticeAttempt, Question
from interview_prep.schemas.content import PracticeAttemptCreate

router = APIRouter(prefix="/practice", tags=["practice"])


@router.post("/attempts", status_code=status.HTTP_202_ACCEPTED)
async def submit_attempt(
    payload: PracticeAttemptCreate, session: SessionDep, user: CurrentUser
) -> dict[str, str]:
    question_exists = await session.scalar(
        select(Question.id).where(Question.id == payload.question_id, Question.is_active.is_(True))
    )
    if question_exists is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")
    attempt = PracticeAttempt(user_id=user.id, **payload.model_dump())
    session.add(attempt)
    await session.flush()

    # AI assessment is asynchronous so user-facing latency and retries are isolated.
    return {"attempt_id": str(attempt.id), "status": "queued_for_evaluation"}
