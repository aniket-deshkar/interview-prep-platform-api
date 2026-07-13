from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.models.entities import MockInterviewSession, Question, Resume
from interview_prep.models.enums import QuestionKind
from interview_prep.schemas.mock import MockSessionCreate

MODE_TO_KIND = {
    "coding": [QuestionKind.DSA, QuestionKind.SQL, QuestionKind.NOSQL, QuestionKind.VECTOR_DB],
    "theory": [QuestionKind.THEORY],
    "data stores": [QuestionKind.SQL, QuestionKind.NOSQL, QuestionKind.VECTOR_DB],
    "system design": [QuestionKind.SYSTEM_DESIGN],
    "behavioural": [QuestionKind.BEHAVIOURAL],
}


async def create_mock_session(
    session: AsyncSession, user_id: UUID, payload: MockSessionCreate
) -> MockInterviewSession:
    if payload.resume_id:
        resume = await session.scalar(
            select(Resume).where(Resume.id == payload.resume_id, Resume.user_id == user_id)
        )
        if resume is None:
            raise LookupError("Resume not found")

    kinds = {
        kind
        for mode in payload.modes
        for kind in MODE_TO_KIND.get(mode.casefold(), [QuestionKind.THEORY])
    }
    questions = list(
        (
            await session.scalars(
                select(Question)
                .where(Question.is_active.is_(True), Question.kind.in_(kinds))
                .order_by(Question.published_at.desc())
                .limit(payload.question_count)
            )
        ).all()
    )
    mock = MockInterviewSession(
        user_id=user_id,
        resume_id=payload.resume_id,
        modes=payload.modes,
        target_role=payload.target_role,
        question_ids=[question.id for question in questions],
        status="ready" if questions else "generating",
    )
    session.add(mock)
    await session.flush()
    return mock
