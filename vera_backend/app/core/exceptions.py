"""
Custom exceptions for Vira backend
"""
from typing import Any, Dict, Optional


class ViraException(Exception):
    """Base exception for Vira application"""

    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class AuthenticationError(ViraException):
    """Authentication related errors"""

    pass


class AuthorizationError(ViraException):
    """Authorization related errors"""

    pass


class ValidationError(ViraException):
    """Data validation errors"""

    pass


class NotFoundError(ViraException):
    """Resource not found errors"""

    pass


class ConflictError(ViraException):
    """Resource conflict errors"""

    pass


class ExternalServiceError(ViraException):
    """External service integration errors"""

    pass


class AIServiceError(ViraException):
    """AI service related errors"""

    pass


class FileProcessingError(ViraException):
    """File processing errors"""

    pass
