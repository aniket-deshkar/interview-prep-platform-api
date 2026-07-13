import asyncio
from datetime import UTC, datetime
from uuid import UUID

import structlog
from celery import shared_task
from openai import AsyncOpenAI
from sqlalchemy import select

from interview_prep.core.config import get_settings
from interview_prep.core.database import SessionFactory
from interview_prep.models.entities import (
    FactCard,
    ProviderConnection,
    Question,
    Resume,
    ResumeChunk,
)
from interview_prep.models.enums import Difficulty, QuestionKind
from interview_prep.services.object_storage import get_object_storage
from interview_prep.services.resume_parser import chunk_text, extract_resume_text

logger = structlog.get_logger()


def _run(coro: object) -> object:
    return asyncio.run(coro)  # type: ignore[arg-type]


@shared_task(  # type: ignore[untyped-decorator]
    name="content.refresh_question_bank",
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
)
def refresh_question_bank() -> dict[str, int]:
    """Refresh curated content once globally, not once per user."""
    return _run(_refresh_question_bank())  # type: ignore[return-value]


async def _refresh_question_bank() -> dict[str, int]:
    # A deterministic seed keeps local development useful. In production this adapter is
    # replaced by an official-source ingestor plus an LLM normalization/evaluation pipeline.
    now = datetime.now(UTC)
    seed = [
        {
            "kind": QuestionKind.DSA,
            "difficulty": Difficulty.MEDIUM,
            "title": "Longest substring without repeating characters",
            "prompt": "Implement a sliding-window solution and explain its invariant.",
            "topic": "Sliding window",
            "source": "LeetCode",
            "external_id": "longest-substring-without-repeating-characters",
            "source_url": "https://leetcode.com/problems/longest-substring-without-repeating-characters/",
        },
        {
            "kind": QuestionKind.THEORY,
            "difficulty": Difficulty.MEDIUM,
            "title": "Spring transaction proxy boundaries",
            "prompt": "Explain why @Transactional self-invocation can bypass transaction advice.",
            "topic": "Spring Boot",
            "source": "Spring Documentation",
            "external_id": "spring-transaction-self-invocation",
            "source_url": "https://docs.spring.io/spring-framework/reference/data-access/transaction/declarative.html",
        },
        {
            "kind": QuestionKind.SQL,
            "difficulty": Difficulty.MEDIUM,
            "title": "Latest recruiter response",
            "prompt": (
                "Return the latest recruiter message per application while retaining "
                "applications with no reply."
            ),
            "topic": "Window functions",
            "source": "SQLZoo",
            "external_id": "latest-recruiter-response-window",
            "source_url": "https://sqlzoo.net/wiki/Window_functions",
        },
    ]
    async with SessionFactory.begin() as session:
        for item in seed:
            existing = await session.scalar(
                select(Question).where(
                    Question.source == item["source"], Question.external_id == item["external_id"]
                )
            )
            if existing:
                for field, value in item.items():
                    setattr(existing, field, value)
                existing.published_at = now
                existing.is_active = True
            else:
                session.add(Question(**item, published_at=now))
        session.add(
            FactCard(
                title="Async improves concurrency, not CPU speed",
                body=(
                    "An event loop serves other work while a coroutine waits; CPU-bound work "
                    "still needs a separate execution strategy."
                ),
                stat="1 loop",
                topic="Python & FastAPI",
                source_name="Python documentation",
                source_url="https://docs.python.org/3/library/asyncio.html",
                published_at=now,
            )
        )
    return {"questions_upserted": len(seed), "facts_created": 1}


@shared_task(  # type: ignore[untyped-decorator]
    name="resumes.parse", autoretry_for=(Exception,), retry_backoff=True, max_retries=3
)
def parse_resume(resume_id: str) -> dict[str, str]:
    return _run(_parse_resume(UUID(resume_id)))  # type: ignore[return-value]


async def _parse_resume(resume_id: UUID) -> dict[str, str]:
    settings = get_settings()
    async with SessionFactory.begin() as session:
        resume = await session.get(Resume, resume_id)
        if resume is None:
            return {"status": "missing"}
        resume.status = "processing"
        data = get_object_storage().download(resume.object_key)
        text = extract_resume_text(data, resume.content_type)
        chunks = chunk_text(text)
        embeddings: list[list[float] | None] = [None] * len(chunks)
        if settings.openai_api_key.get_secret_value():
            client = AsyncOpenAI(api_key=settings.openai_api_key.get_secret_value())
            result = await client.embeddings.create(model=settings.embedding_model, input=chunks)
            embeddings = [item.embedding for item in result.data]
        session.add_all(
            [
                ResumeChunk(
                    resume_id=resume.id,
                    user_id=resume.user_id,
                    ordinal=index,
                    content=chunk,
                    source_label=f"{resume.file_name} · section {index + 1}",
                    embedding=embeddings[index],
                )
                for index, chunk in enumerate(chunks)
            ]
        )
        resume.extracted_text = text
        resume.parsed_profile = {"character_count": len(text), "chunk_count": len(chunks)}
        resume.status = "ready"
    return {"status": "ready"}


@shared_task(name="integrations.sync_calendars")  # type: ignore[untyped-decorator]
def sync_calendars() -> dict[str, int]:
    return _run(_count_active_connections())  # type: ignore[return-value]


@shared_task(name="integrations.sync_recruiter_mail")  # type: ignore[untyped-decorator]
def sync_recruiter_mail() -> dict[str, int]:
    return _run(_count_active_connections())  # type: ignore[return-value]


async def _count_active_connections() -> dict[str, int]:
    async with SessionFactory() as session:
        connections = list(
            (
                await session.scalars(
                    select(ProviderConnection).where(ProviderConnection.is_active.is_(True))
                )
            ).all()
        )
    logger.info("provider_sync_batch", connections=len(connections))
    return {"connections": len(connections)}
