from fastapi import APIRouter

from interview_prep.api.routes import auth, content, integrations, mock, practice, resumes, tracker

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(content.router)
api_router.include_router(resumes.router)
api_router.include_router(mock.router)
api_router.include_router(practice.router)
api_router.include_router(tracker.router)
api_router.include_router(integrations.router)
