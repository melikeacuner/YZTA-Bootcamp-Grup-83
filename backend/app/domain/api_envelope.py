from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Tum API yanitlarinin ortak zarfi: status/data/error birbirini disliyarak doldurulur."""

    status: str
    data: T | None = None
    error: str | None = None

    @classmethod
    def ok(cls, data: T) -> "APIResponse[T]":
        return cls(status="success", data=data, error=None)

    @classmethod
    def fail(cls, error: str) -> "APIResponse[None]":
        return cls(status="error", data=None, error=error)
