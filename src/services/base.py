"""Base services module."""
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from sqlalchemy.orm import Session

from exceptions import base as base_exceptions
from paginator import BasePaginator
from schemas.base import PaginatedResponse

T = TypeVar("T")


@dataclass
class BaseService(Generic[T]):
    """
    Base service class with database operation for models.

    Inheriting class must override following fields: model.

    class SampleService(CreateServiceMixin, BaseService):
        model = SampleModel

    """

    model: ClassVar[T]
    session: Session
    _paginator: BasePaginator | None = None

    def _get_by_pk(self, pk: Any) -> Any:
        """Returns item with matching pk, or None if item is not found."""
        return self.session.query(self.model).get(pk)

    def set_paginator(self, paginator: BasePaginator):
        """Set paginator for service"""
        self._paginator = paginator

    def get_or_404(self, pk: Any) -> Any:
        """Returns item with matching pk. If nothing found raises NotFound."""
        item = self._get_by_pk(pk)
        if item is None:
            raise base_exceptions.NotFound
        return item


class ListMixin(BaseService[T]):
    """Mixin class for all() operation."""

    def all(self) -> PaginatedResponse[T] | list[T]:
        """Returns list of all records."""
        query = self.session.query(self.model)

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()


class CreateServiceMixin(BaseService[T]):
    """Mixin class for create() operation."""

    def create(self, schema: dict[str, Any]) -> T:
        """Creates and returns item."""
        item = self.model(**schema)
        self.session.add(item)
        self.session.commit()
        return item


class UpdateServiceMixin(BaseService[T]):
    """Mixin with update() operation."""

    def update(self, pk, schema: Mapping[str, Any]) -> T:
        """Updates and returns updated item."""
        item = self.get_or_404(pk)

        for field, value in schema.items():
            if value is not None:
                setattr(item, field, value)

        self.session.commit()
        self.session.refresh(item)
        return item


class DeleteServiceMixin(BaseService[T]):
    """Mixin with delete() operation."""

    def delete(self, pk: Any) -> None:
        """Deletes item with given pk."""
        item = self.get_or_404(pk)
        self.session.delete(item)
        self.session.commit()


class CreateUpdateDeleteService(
    CreateServiceMixin[T],
    UpdateServiceMixin[T],
    DeleteServiceMixin[T],
    BaseService[T],
):
    """Service with create, update and delete methods."""
