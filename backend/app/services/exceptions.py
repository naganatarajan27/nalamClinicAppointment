class DomainError(Exception):
    """Base class for service-layer errors the API layer maps to HTTP responses."""


class NotFoundError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class InvalidTransitionError(DomainError):
    pass
