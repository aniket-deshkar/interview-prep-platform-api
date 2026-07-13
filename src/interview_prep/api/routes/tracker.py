from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select

from interview_prep.api.dependencies import CurrentUser, SessionDep
from interview_prep.models.entities import Interview
from interview_prep.repositories.applications import ApplicationRepository
from interview_prep.schemas.tracker import (
    ApplicationCreate,
    ApplicationResponse,
    ApplicationUpdate,
    InterviewCreate,
    InterviewResponse,
)

router = APIRouter(prefix="/tracker", tags=["tracker"])


@router.get("/applications", response_model=list[ApplicationResponse])
async def list_applications(
    session: SessionDep,
    user: CurrentUser,
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[ApplicationResponse]:
    items, _ = await ApplicationRepository(session).list_for_user(
        user.id, limit=limit, offset=offset
    )
    return [ApplicationResponse.model_validate(item) for item in items]


@router.post(
    "/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED
)
async def create_application(
    payload: ApplicationCreate, session: SessionDep, user: CurrentUser
) -> ApplicationResponse:
    item = await ApplicationRepository(session).create(user.id, payload)
    return ApplicationResponse.model_validate(item)


@router.patch("/applications/{application_id}", response_model=ApplicationResponse)
async def update_application(
    application_id: UUID,
    payload: ApplicationUpdate,
    session: SessionDep,
    user: CurrentUser,
) -> ApplicationResponse:
    repository = ApplicationRepository(session)
    item = await repository.get_owned(application_id, user.id)
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    item = await repository.update(item, payload)
    return ApplicationResponse.model_validate(item)


@router.get("/interviews", response_model=list[InterviewResponse])
async def list_interviews(session: SessionDep, user: CurrentUser) -> list[Interview]:
    return list(
        (
            await session.scalars(
                select(Interview)
                .where(Interview.user_id == user.id)
                .order_by(Interview.starts_at.asc())
            )
        ).all()
    )


@router.post("/interviews", response_model=InterviewResponse, status_code=status.HTTP_201_CREATED)
async def create_interview(
    payload: InterviewCreate, session: SessionDep, user: CurrentUser
) -> Interview:
    item = Interview(user_id=user.id, **payload.model_dump())
    session.add(item)
    await session.flush()
    return item
