"""
Application exception hierarchy.

Improvements:
- Base AppError carries code for client-side handling, plus optional details.
- Specific errors have clear messages and proper HTTP status codes.
- Added ConflictError, BadRequestError, and ServiceUnavailable for broader coverage.
- All errors log via logger when raised? Not here, but handlers will log.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException, status


class AppError(HTTPException):
    """
    Base application error with machine-readable code.
    Extends FastAPI HTTPException to be caught by global handler.
    """

    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        code: str = "internal_error",
        headers: dict[str, str] | None = None,
        extra: dict[str, Any] | None = None,
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.code = code
        self.extra = extra or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(code={self.code}, status={self.status_code}, detail={self.detail})"


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found"
        if identifier:
            # Truncate identifier to avoid leaking long secrets
            safe_id = str(identifier)[:100]
            detail = f"{resource} '{safe_id}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code="not_found",
        )


class AuthError(AppError):
    def __init__(
        self,
        detail: str = "Authentication failed",
        headers: dict[str, str] | None = None,
    ):
        # For 401, include WWW-Authenticate header as per RFC
        hdrs = headers or {"WWW-Authenticate": "Bearer"}
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="auth_error",
            headers=hdrs,
        )


class ForbiddenError(AppError):
    def __init__(
        self, detail: str = "You do not have permission to perform this action"
    ):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="forbidden",
        )


class ValidationError(AppError):
    def __init__(
        self, detail: str = "Validation failed", extra: dict[str, Any] | None = None
    ):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code="validation_error",
            extra=extra,
        )


class BadRequestError(AppError):
    def __init__(self, detail: str = "Bad request"):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            code="bad_request",
        )


class ConflictError(AppError):
    def __init__(self, detail: str = "Conflict"):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
            code="conflict",
        )


class CreditLimitError(AppError):
    def __init__(self, detail: str = "Insufficient credits"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            code="insufficient_credits",
        )


class RateLimitError(AppError):
    def __init__(
        self, detail: str = "Too many requests. Please try again later.", retry_after: int | None = None
    ):
        headers = {}
        if retry_after:
            headers["Retry-After"] = str(retry_after)
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            code="rate_limit_exceeded",
            headers=headers or None,
        )


class AIServiceError(AppError):
    def __init__(self, detail: str = "AI service error", provider: str = ""):
        msg = f"{provider}: {detail}" if provider else detail
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=msg,
            code="ai_service_error",
        )


class ProviderOverloadedError(AppError):
    def __init__(self, provider: str = ""):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"AI provider{'(' + provider + ')' if provider else ''} is currently overloaded",
            code="provider_overloaded",
        )


class ProviderRateLimitError(AppError):
    def __init__(self, provider: str = "", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"AI provider{'(' + provider + ')' if provider else ''} rate limit exceeded. Retry after {retry_after}s",
            code="provider_rate_limit",
            headers={"Retry-After": str(retry_after)},
        )


class ModelNotFoundError(AppError):
    def __init__(self, model: str = ""):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model}' not found or not available"
            if model
            else "Model not found",
            code="model_not_found",
        )


class ServiceUnavailableError(AppError):
    def __init__(self, detail: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=detail,
            code="service_unavailable",
        )
