from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MockSessionCreate(BaseModel):
    target_role: str = Field(min_length=2, max_length=200)
    modes: list[str] = Field(min_length=1, max_length=5)
    resume_id: UUID | None = None
    question_count: int = Field(default=8, ge=3, le=20)


class MockSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    target_role: str
    modes: list[str]
    resume_id: UUID | None
    status: str
    question_ids: list[UUID]
    score: int | None
    report: dict[str, object]
    created_at: datetime
