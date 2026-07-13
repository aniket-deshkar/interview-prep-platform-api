from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from interview_prep.models.enums import ApplicationStage


class ApplicationCreate(BaseModel):
    company: str = Field(min_length=1, max_length=160)
    role: str = Field(min_length=1, max_length=200)
    stage: ApplicationStage = ApplicationStage.SAVED
    source: str | None = Field(default=None, max_length=120)
    recruiter_name: str | None = Field(default=None, max_length=160)
    recruiter_email: str | None = Field(default=None, max_length=320)
    compensation_amount: float | None = Field(default=None, ge=0)
    compensation_currency: str | None = Field(default=None, min_length=3, max_length=3)
    compensation_period: str | None = Field(default=None, max_length=20)
    next_action_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=20_000)
    url: str | None = Field(default=None, max_length=1000)


class ApplicationUpdate(BaseModel):
    stage: ApplicationStage | None = None
    recruiter_name: str | None = Field(default=None, max_length=160)
    recruiter_email: str | None = Field(default=None, max_length=320)
    compensation_amount: float | None = Field(default=None, ge=0)
    compensation_currency: str | None = Field(default=None, min_length=3, max_length=3)
    compensation_period: str | None = Field(default=None, max_length=20)
    next_action_at: datetime | None = None
    notes: str | None = Field(default=None, max_length=20_000)


class ApplicationResponse(ApplicationCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class InterviewCreate(BaseModel):
    application_id: UUID | None = None
    round_name: str = Field(min_length=1, max_length=160)
    starts_at: datetime
    ends_at: datetime | None = None
    meeting_url: str | None = Field(default=None, max_length=1000)
    interviewer_names: list[str] = Field(default_factory=list, max_length=20)
    preparation_notes: str | None = Field(default=None, max_length=20_000)

    @model_validator(mode="after")
    def end_must_follow_start(self) -> "InterviewCreate":
        if self.ends_at and self.ends_at <= self.starts_at:
            raise ValueError("ends_at must be after starts_at")
        return self


class InterviewResponse(InterviewCreate):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    retrospective_notes: str | None
    created_at: datetime
    updated_at: datetime
