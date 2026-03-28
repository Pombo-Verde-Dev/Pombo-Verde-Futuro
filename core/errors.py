from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiohttp import ClientResponse

__all__ = (
    "SalaFuturoError",
    "AuthenticationError",
    "APIError",
    "RateLimitError",
    "NotFoundError",
    "ForbiddenError",
    "ValidationError",
    "CacheError",
)


class SalaFuturoError(Exception):
    def __init__(self, message: str | None = None) -> None:
        self.message = message or "An unknown error occurred"
        super().__init__(self.message)


class AuthenticationError(SalaFuturoError):
    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message)


class APIError(SalaFuturoError):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        url: str | None = None,
        method: str | None = None,
        body: str | None = None,
        response: ClientResponse | None = None,
    ) -> None:
        self.status_code = status_code
        self.url = url
        self.method = method
        self.body = body
        self.response = response

        parts = []
        if status_code:
            parts.append(f"[{status_code}]")
        parts.append(message)
        if url and method:
            parts.append(f"→ {method} {url}")

        super().__init__(" ".join(parts))


class RateLimitError(APIError):
    def __init__(
        self,
        retry_after: float,
        *,
        url: str | None = None,
        method: str | None = None,
    ) -> None:
        self.retry_after = retry_after
        super().__init__(
            f"Rate limited. Retry after {retry_after:.2f}s",
            status_code=429,
            url=url,
            method=method,
        )


class NotFoundError(APIError):
    def __init__(self, resource: str, *, url: str | None = None) -> None:
        self.resource = resource
        super().__init__(
            f"{resource} not found",
            status_code=404,
            url=url,
        )


class ForbiddenError(APIError):
    def __init__(
        self,
        message: str = "Access forbidden",
        *,
        url: str | None = None,
    ) -> None:
        super().__init__(message, status_code=403, url=url)


class ValidationError(SalaFuturoError):
    def __init__(self, field: str, message: str) -> None:
        self.field = field
        self.message = message
        super().__init__(f"Validation error for '{field}': {message}")


class CacheError(SalaFuturoError):
    pass