from pydantic import BaseModel


class MessageResponse(BaseModel):
    message: str


class PageMeta(BaseModel):
    limit: int
    offset: int
    total: int


class ErrorDetail(BaseModel):
    code: str
    message: str
    request_id: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorDetail
