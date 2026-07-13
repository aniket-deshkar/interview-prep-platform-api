from datetime import UTC, datetime
from typing import cast
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from interview_prep.models.entities import ApplicationStageEvent, JobApplication
from interview_prep.schemas.tracker import ApplicationCreate, ApplicationUpdate


class ApplicationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_for_user(
        self, user_id: UUID, *, limit: int, offset: int
    ) -> tuple[list[JobApplication], int]:
        base: Select[tuple[JobApplication]] = select(JobApplication).where(
            JobApplication.user_id == user_id
        )
        items = list(
            (
                await self.session.scalars(
                    base.order_by(JobApplication.updated_at.desc()).limit(limit).offset(offset)
                )
            ).all()
        )
        total = await self.session.scalar(
            select(func.count())
            .select_from(JobApplication)
            .where(JobApplication.user_id == user_id)
        )
        return items, int(total or 0)

    async def create(self, user_id: UUID, payload: ApplicationCreate) -> JobApplication:
        application = JobApplication(user_id=user_id, **payload.model_dump())
        self.session.add(application)
        await self.session.flush()
        self.session.add(
            ApplicationStageEvent(
                application_id=application.id,
                stage=application.stage,
                occurred_at=datetime.now(UTC),
                source="manual",
            )
        )
        return application

    async def get_owned(self, application_id: UUID, user_id: UUID) -> JobApplication | None:
        return cast(
            JobApplication | None,
            await self.session.scalar(
                select(JobApplication).where(
                    JobApplication.id == application_id, JobApplication.user_id == user_id
                )
            ),
        )

    async def update(
        self, application: JobApplication, payload: ApplicationUpdate
    ) -> JobApplication:
        previous_stage = application.stage
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(application, field, value)
        if payload.stage is not None and payload.stage != previous_stage:
            self.session.add(
                ApplicationStageEvent(
                    application_id=application.id,
                    stage=payload.stage,
                    occurred_at=datetime.now(UTC),
                    source="manual",
                )
            )
        await self.session.flush()
        return application
