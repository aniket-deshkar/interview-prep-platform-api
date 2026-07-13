from pathlib import Path
from typing import Annotated
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from sqlalchemy import select

from interview_prep.api.dependencies import CurrentUser, SessionDep
from interview_prep.models.entities import Resume
from interview_prep.schemas.resume import ResumeResponse
from interview_prep.services.object_storage import get_object_storage

router = APIRouter(prefix="/resumes", tags=["resumes"])
ALLOWED_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_FILE_SIZE = 10 * 1024 * 1024


@router.get("", response_model=list[ResumeResponse])
async def list_resumes(session: SessionDep, user: CurrentUser) -> list[Resume]:
    return list(
        (
            await session.scalars(
                select(Resume).where(Resume.user_id == user.id).order_by(Resume.created_at.desc())
            )
        ).all()
    )


@router.post("", response_model=ResumeResponse, status_code=status.HTTP_202_ACCEPTED)
async def upload_resume(
    session: SessionDep, user: CurrentUser, file: Annotated[UploadFile, File()]
) -> Resume:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail="Use PDF or DOCX"
        )
    data = await file.read(MAX_FILE_SIZE + 1)
    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="Maximum size is 10 MB"
        )
    safe_suffix = Path(file.filename or "resume.pdf").suffix.lower()
    object_key = f"users/{user.id}/resumes/{uuid4()}{safe_suffix}"

    from io import BytesIO

    get_object_storage().upload(object_key, BytesIO(data), file.content_type)
    resume = Resume(
        user_id=user.id,
        file_name=Path(file.filename or "resume").name,
        object_key=object_key,
        content_type=file.content_type,
        size_bytes=len(data),
        status="queued",
    )
    session.add(resume)
    await session.flush()

    from interview_prep.worker.tasks import parse_resume

    parse_resume.delay(str(resume.id))
    return resume
