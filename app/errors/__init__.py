class DomainError(Exception):
    status_code = 400
    code = "DOMAIN_ERROR"

    def __init__(self, message: str | None = None):
        super().__init__(message or self.code)


class ValidationError(DomainError):
    status_code = 400
    code = "VALIDATION_ERROR"


class NotFoundError(DomainError):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(DomainError):
    status_code = 409
    code = "CONFLICT"


class LifecycleError(DomainError):
    status_code = 409
    code = "LIFECYCLE_CONFLICT"


__all__ = [
    "ConflictError",
    "DomainError",
    "LifecycleError",
    "NotFoundError",
    "ValidationError",
]
