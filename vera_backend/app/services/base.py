"""
Base service class implementing the Service Layer pattern
"""
from abc import ABC
from typing import Generic, TypeVar

from sqlalchemy.orm import Session

from app.core.exceptions import ViraException

T = TypeVar("T")


class BaseService(Generic[T], ABC):
    """
    Base service class providing common business logic patterns
    Implements the Service Layer pattern for business logic encapsulation
    """

    def __init__(self, db: Session):
        self.db = db

    def _validate_business_rules(self, *args, **kwargs) -> None:
        """
        Template method for business rule validation
        Override in concrete service classes
        """
        pass

    def _handle_transaction(self, operation, *args, **kwargs):
        """
        Handle database transactions with proper rollback
        """
        try:
            result = operation(*args, **kwargs)
            self.db.commit()
            return result
        except Exception as e:
            self.db.rollback()
            raise ViraException(f"Transaction failed: {str(e)}")

    def _log_operation(self, operation: str, entity_id: str, details: dict = None):
        """
        Log business operations for audit trail
        Can be extended to integrate with proper logging system
        """
        # TODO: Implement proper audit logging
        pass
