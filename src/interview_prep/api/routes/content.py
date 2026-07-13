from fastapi import APIRouter, Query
from sqlalchemy import ColumnElement, func, select

from interview_prep.api.dependencies import CurrentUser, SessionDep
from interview_prep.models.entities import FactCard, Question
from interview_prep.models.enums import Difficulty, QuestionKind
from interview_prep.schemas.content import FactCardResponse, QuestionPage

router = APIRouter(prefix="/content", tags=["content"])


@router.get("/questions", response_model=QuestionPage)
async def list_questions(
    session: SessionDep,
    _: CurrentUser,
    kind: QuestionKind | None = None,
    difficulty: Difficulty | None = None,
    topic: str | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> QuestionPage:
    filters: list[ColumnElement[bool]] = [Question.is_active.is_(True)]
    if kind:
        filters.append(Question.kind == kind)
    if difficulty:
        filters.append(Question.difficulty == difficulty)
    if topic:
        filters.append(Question.topic == topic)
    items = list(
        (
            await session.scalars(
                select(Question)
                .where(*filters)
                .order_by(Question.published_at.desc())
                .limit(limit)
                .offset(offset)
            )
        ).all()
    )
    total = await session.scalar(select(func.count()).select_from(Question).where(*filters))
    return QuestionPage(items=items, total=int(total or 0), limit=limit, offset=offset)


@router.get("/fact-card", response_model=FactCardResponse)
async def latest_fact_card(session: SessionDep, _: CurrentUser) -> FactCard:
    fact = await session.scalar(
        select(FactCard)
        .where(FactCard.is_active.is_(True))
        .order_by(FactCard.published_at.desc())
        .limit(1)
    )
    if fact is None:
        from fastapi import HTTPException, status

        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No fact card available")
    return fact
