from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from interview_prep.models.enums import Difficulty, QuestionKind


class QuestionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    kind: QuestionKind
    difficulty: Difficulty
    title: str
    prompt: str
    explanation: str | None
    topic: str
    source: str
    source_url: str | None
    published_at: datetime


class QuestionPage(BaseModel):
    items: list[QuestionResponse]
    total: int
    limit: int
    offset: int


class FactCardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    body: str
    stat: str | None
    topic: str
    source_name: str
    source_url: str
    published_at: datetime


class PracticeAttemptCreate(BaseModel):
    question_id: UUID
    answer: str = Field(min_length=1, max_length=50_000)
    language: str | None = Field(default=None, max_length=40)
    duration_seconds: int | None = Field(default=None, ge=0, le=86_400)
