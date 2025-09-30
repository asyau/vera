"""
Base repository class implementing the Repository pattern
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar
from uuid import UUID

from sqlalchemy import and_, or_
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError

T = TypeVar("T")


class BaseRepository(Generic[T], ABC):
    """
    Base repository class providing common CRUD operations
    Implements the Repository pattern for data access abstraction
    """

    def __init__(self, db: Session, model: Type[T]):
        self.db = db
        self.model = model

    def get(self, id: UUID) -> Optional[T]:
        """Get a single record by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first()

    def get_or_raise(self, id: UUID) -> T:
        """Get a single record by ID or raise NotFoundError"""
        instance = self.get(id)
        if not instance:
            raise NotFoundError(
                f"{self.model.__name__} with id {id} not found",
                error_code="RESOURCE_NOT_FOUND",
            )
        return instance

    def get_all(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> List[T]:
        """Get all records with optional filtering and pagination"""
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.offset(skip).limit(limit).all()

    def create(self, obj_data: Dict[str, Any]) -> T:
        """Create a new record"""
        try:
            db_obj = self.model(**obj_data)
            self.db.add(db_obj)
            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except Exception as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to create {self.model.__name__}: {str(e)}",
                error_code="CREATE_FAILED",
            )

    def update(self, id: UUID, obj_data: Dict[str, Any]) -> T:
        """Update an existing record"""
        db_obj = self.get_or_raise(id)

        try:
            for key, value in obj_data.items():
                if hasattr(db_obj, key):
                    setattr(db_obj, key, value)

            self.db.commit()
            self.db.refresh(db_obj)
            return db_obj
        except Exception as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to update {self.model.__name__}: {str(e)}",
                error_code="UPDATE_FAILED",
            )

    def delete(self, id: UUID) -> bool:
        """Delete a record by ID"""
        db_obj = self.get_or_raise(id)

        try:
            self.db.delete(db_obj)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            raise ValidationError(
                f"Failed to delete {self.model.__name__}: {str(e)}",
                error_code="DELETE_FAILED",
            )

    def count(self, filters: Optional[Dict[str, Any]] = None) -> int:
        """Count records with optional filtering"""
        query = self.db.query(self.model)

        if filters:
            for key, value in filters.items():
                if hasattr(self.model, key):
                    query = query.filter(getattr(self.model, key) == value)

        return query.count()

    def exists(self, id: UUID) -> bool:
        """Check if a record exists by ID"""
        return self.db.query(self.model).filter(self.model.id == id).first() is not None

    @abstractmethod
    def get_by_filters(self, **filters) -> List[T]:
        """
        Abstract method for custom filtering logic
        Should be implemented by concrete repository classes
        """
        pass
