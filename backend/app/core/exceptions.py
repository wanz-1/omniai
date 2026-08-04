from fastapi import HTTPException, status


class AppError(HTTPException):
    def __init__(
        self,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail: str = "An unexpected error occurred",
        code: str = "internal_error",
    ):
        super().__init__(status_code=status_code, detail=detail)
        self.code = code


class NotFoundError(AppError):
    def __init__(self, resource: str = "Resource", identifier: str = ""):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} '{identifier}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            code="not_found",
        )


class AuthError(AppError):
    def __init__(self, detail: str = "Authentication failed"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            code="auth_error",
        )


class ForbiddenError(AppError):
    def __init__(self, detail: str = "You do not have permission to perform this action"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            code="forbidden",
        )


class ValidationError(AppError):
    def __init__(self, detail: str = "Validation failed"):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            code="validation_error",
        )


class CreditLimitError(AppError):
    def __init__(self, detail: str = "Insufficient credits"):
        super().__init__(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=detail,
            code="insufficient_credits",
        )


class RateLimitError(AppError):
    def __init__(self, detail: str = "Too many requests. Please try again later."):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            code="rate_limit_exceeded",
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
            detail=f"AI provider {'(' + provider + ')' if provider else ''} is currently overloaded",
            code="provider_overloaded",
        )


class ProviderRateLimitError(AppError):
    def __init__(self, provider: str = "", retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"AI provider {'(' + provider + ')' if provider else ''} rate limit exceeded. Retry after {retry_after}s",
            code="provider_rate_limit",
        )


class ModelNotFoundError(AppError):
    def __init__(self, model: str = ""):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model}' not found or not available" if model else "Model not found",
            code="model_not_found",
        )
