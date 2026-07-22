from typing import Generic, TypeVar

from pydantic import BaseModel, Field


DataT = TypeVar("DataT")


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


class CursorPage(BaseModel, Generic[DataT]):
    items: list[DataT]

    next_cursor: str | None = None

    has_more: bool = False


class PaginationQuery(BaseModel):
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
    )

    cursor: str | None = None