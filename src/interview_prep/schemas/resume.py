from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class ResumeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    file_name: str
    content_type: str
    size_bytes: int
    status: str
    is_primary: bool
    parsed_profile: dict[str, object]
    created_at: datetime
