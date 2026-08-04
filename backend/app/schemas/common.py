import uuid
from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel


T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    limit: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    code: str | None = None


class MessageResponse(BaseModel):
    message: str


class IDResponse(BaseModel):
    id: uuid.UUID
