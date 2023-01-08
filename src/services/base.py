"""Base services module."""
from dataclasses import dataclass
from typing import Any, ClassVar

from sqlalchemy.orm import Session

from exceptions import base as base_exceptions
from paginator import BasePaginator
from schemas.base import BaseModel


@dataclass
class BaseService:
    """
    Base service class with database operation for models.

    Inheriting class must override following fields: model.

    class SampleService(CreateServiceMixin, BaseService):
        model = SampleModel

    """

    model: ClassVar[Any]
    session: Session
    _paginator: BasePaginator | None = None

    def _get_by_pk(self, pk: Any) -> Any:
        """Returns item with matching pk, or None if item is not found."""
        return self.session.query(self.model).get(pk)

    def set_paginator(self, paginator: BasePaginator):
        """Set paginator for service"""
        self._paginator = paginator

    def all(self):
        """Returns list of all records."""
        query = self.session.query(self.model)

        if self._paginator:
            return self._paginator.get_paginated_response(query)

        return query.all()

    def get_or_404(self, pk: Any) -> Any:
        """Returns item with matching pk. If nothing found raises NotFound."""
        item = self._get_by_pk(pk)
        if item is None:
            raise base_exceptions.NotFound
        return item


class CreateServiceMixin(BaseService):
    """Mixin class for create() operation."""

    def create(self, schema: BaseModel) -> Any:
        """Creates and returns item."""
        item = self.model(**schema.dict())
        self.session.add(item)
        self.session.commit()
        return item


class UpdateServiceMixin(BaseService):
    """Mixin with update() operation."""

    def update(self, pk, schema: BaseModel) -> Any:
        """Updates and returns updated item."""
        item = self.get_or_404(pk)

        for field, value in schema.dict().items():
            if value is not None:
                setattr(item, field, value)

        self.session.commit()
        self.session.refresh(item)
        return item


class DeleteServiceMixin(BaseService):
    """Mixin with delete() operation."""

    def delete(self, pk: Any) -> None:
        """Deletes item with given pk."""
        item = self.get_or_404(pk)
        self.session.delete(item)
        self.session.commit()


class CreateUpdateDeleteService(
    CreateServiceMixin, UpdateServiceMixin, DeleteServiceMixin, BaseService
):
    """Service with create, update and delete methods."""
