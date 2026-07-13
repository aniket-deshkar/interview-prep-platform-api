from contextlib import asynccontextmanager
from typing import Any
from uuid import uuid4

import structlog
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app
from structlog.contextvars import bind_contextvars, clear_contextvars

from interview_prep.api.router import api_router
from interview_prep.api.routes.health import router as health_router
from interview_prep.core.config import get_settings
from interview_prep.core.database import engine
from interview_prep.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.debug)
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(_: FastAPI) -> Any:
    logger.info("application_started", environment=settings.environment)
    yield
    await engine.dispose()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Resume-aware interview preparation and job-tracking API.",
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
)


@app.middleware("http")
async def request_context(request: Request, call_next: Any) -> Any:
    clear_contextvars()
    request_id = request.headers.get("X-Request-ID", str(uuid4()))
    bind_contextvars(request_id=request_id, method=request.method, path=request.url.path)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


app.include_router(health_router)
app.include_router(api_router, prefix=settings.api_v1_prefix)
app.mount("/metrics", make_asgi_app())
