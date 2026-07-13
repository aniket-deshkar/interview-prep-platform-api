from celery import Celery
from celery.schedules import crontab

from interview_prep.core.config import get_settings

settings = get_settings()
celery_app = Celery(
    "interview_prep",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["interview_prep.worker.tasks"],
)
celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    timezone="UTC",
    beat_schedule={
        "refresh-question-bank-every-six-hours": {
            "task": "content.refresh_question_bank",
            "schedule": crontab(minute=5, hour="*/6"),
        },
        "sync-connected-calendars-every-fifteen-minutes": {
            "task": "integrations.sync_calendars",
            "schedule": crontab(minute="*/15"),
        },
        "sync-recruiter-mail-hourly": {
            "task": "integrations.sync_recruiter_mail",
            "schedule": crontab(minute=20),
        },
    },
)
