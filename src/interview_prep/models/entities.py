from datetime import datetime
from typing import Any
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from interview_prep.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin
from interview_prep.models.enums import ApplicationStage, Difficulty, Provider, QuestionKind


class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(120))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    target_roles: Mapped[list[str]] = mapped_column(ARRAY(String(120)), default=list)


class Resume(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resumes"

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(255))
    object_key: Mapped[str] = mapped_column(String(512), unique=True)
    content_type: Mapped[str] = mapped_column(String(120))
    size_bytes: Mapped[int] = mapped_column(BigInteger)
    status: Mapped[str] = mapped_column(String(32), default="uploaded", index=True)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    parsed_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")


class ResumeChunk(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "resume_chunks"
    __table_args__ = (
        Index(
            "ix_resume_chunks_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    resume_id: Mapped[UUID] = mapped_column(
        ForeignKey("resumes.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    ordinal: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    source_label: Mapped[str] = mapped_column(String(160))
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))


class Question(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "questions"
    __table_args__ = (
        UniqueConstraint("source", "external_id"),
        Index("ix_questions_discovery", "kind", "difficulty", "is_active", "published_at"),
        Index(
            "ix_questions_embedding_hnsw",
            "embedding",
            postgresql_using="hnsw",
            postgresql_ops={"embedding": "vector_cosine_ops"},
        ),
    )

    kind: Mapped[QuestionKind] = mapped_column(Enum(QuestionKind, name="question_kind"))
    difficulty: Mapped[Difficulty] = mapped_column(Enum(Difficulty, name="difficulty"))
    title: Mapped[str] = mapped_column(String(240))
    prompt: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str | None] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(120), index=True)
    source: Mapped[str] = mapped_column(String(80))
    external_id: Mapped[str] = mapped_column(String(200))
    source_url: Mapped[str | None] = mapped_column(String(1000))
    metadata_: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, default=dict)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class FactCard(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "fact_cards"
    __table_args__ = (Index("ix_fact_cards_current", "is_active", "published_at"),)

    title: Mapped[str] = mapped_column(String(180))
    body: Mapped[str] = mapped_column(Text)
    stat: Mapped[str | None] = mapped_column(String(32))
    topic: Mapped[str] = mapped_column(String(120))
    source_name: Mapped[str] = mapped_column(String(120))
    source_url: Mapped[str] = mapped_column(String(1000))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class JobApplication(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "job_applications"
    __table_args__ = (
        Index("ix_job_applications_user_stage", "user_id", "stage", "updated_at"),
        Index("ix_job_applications_next_action", "user_id", "next_action_at"),
    )

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    company: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(200))
    stage: Mapped[ApplicationStage] = mapped_column(
        Enum(ApplicationStage, name="application_stage"), default=ApplicationStage.SAVED
    )
    source: Mapped[str | None] = mapped_column(String(120))
    recruiter_name: Mapped[str | None] = mapped_column(String(160))
    recruiter_email: Mapped[str | None] = mapped_column(String(320))
    compensation_amount: Mapped[float | None] = mapped_column(Numeric(14, 2))
    compensation_currency: Mapped[str | None] = mapped_column(String(3))
    compensation_period: Mapped[str | None] = mapped_column(String(20))
    next_action_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    url: Mapped[str | None] = mapped_column(String(1000))
    stages: Mapped[list["ApplicationStageEvent"]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )


class ApplicationStageEvent(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "application_stage_events"
    __table_args__ = (Index("ix_stage_events_timeline", "application_id", "occurred_at"),)

    application_id: Mapped[UUID] = mapped_column(
        ForeignKey("job_applications.id", ondelete="CASCADE"), index=True
    )
    stage: Mapped[ApplicationStage] = mapped_column(
        Enum(ApplicationStage, name="application_stage")
    )
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(32), default="manual")
    application: Mapped[JobApplication] = relationship(back_populates="stages")


class Interview(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "interviews"
    __table_args__ = (Index("ix_interviews_schedule", "user_id", "starts_at"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    application_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("job_applications.id", ondelete="SET NULL"), index=True
    )
    round_name: Mapped[str] = mapped_column(String(160))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    meeting_url: Mapped[str | None] = mapped_column(String(1000))
    interviewer_names: Mapped[list[str]] = mapped_column(ARRAY(String(160)), default=list)
    preparation_notes: Mapped[str | None] = mapped_column(Text)
    retrospective_notes: Mapped[str | None] = mapped_column(Text)
    external_calendar_id: Mapped[str | None] = mapped_column(String(512))


class PracticeAttempt(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "practice_attempts"
    __table_args__ = (Index("ix_attempts_user_recent", "user_id", "created_at"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    question_id: Mapped[UUID] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), index=True
    )
    language: Mapped[str | None] = mapped_column(String(40))
    answer: Mapped[str] = mapped_column(Text)
    score: Mapped[int | None] = mapped_column(Integer)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    duration_seconds: Mapped[int | None] = mapped_column(Integer)


class MockInterviewSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "mock_interview_sessions"
    __table_args__ = (Index("ix_mock_sessions_user_recent", "user_id", "created_at"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    resume_id: Mapped[UUID | None] = mapped_column(ForeignKey("resumes.id", ondelete="SET NULL"))
    modes: Mapped[list[str]] = mapped_column(ARRAY(String(40)))
    target_role: Mapped[str] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(String(32), default="created", index=True)
    question_ids: Mapped[list[UUID]] = mapped_column(ARRAY(PGUUID(as_uuid=True)), default=list)
    score: Mapped[int | None] = mapped_column(Integer)
    report: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class ProviderConnection(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "provider_connections"
    __table_args__ = (UniqueConstraint("user_id", "provider"),)

    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    provider: Mapped[Provider] = mapped_column(Enum(Provider, name="provider"))
    provider_account_id: Mapped[str] = mapped_column(String(320))
    encrypted_refresh_token: Mapped[str] = mapped_column(Text)
    scopes: Mapped[list[str]] = mapped_column(ARRAY(String(200)), default=list)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sync_cursor: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
