"""Base services module."""
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, ClassVar, Generic, TypeVar

from sqlalchemy import delete, inspect, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.exceptions import base as base_exceptions
from src.paginator import BasePaginator
from src.schemas.base import PaginatedResponse

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
    session: AsyncSession
    _paginator: BasePaginator | None = None

    async def _get_by_pk(self, pk: Any) -> Any:
        """Returns item with matching pk, or None if item is not found."""
        query = select(inspect(self.model).c).where(self.model.id == pk)
        result = await self.session.execute(query)
        return result.fetchone()

    def set_paginator(self, paginator: BasePaginator):
        """Set paginator for service"""
        self._paginator = paginator

    async def get_or_404(self, pk: Any) -> Any:
        """Returns item with matching pk. If nothing found raises NotFound."""
        item = await self._get_by_pk(pk)
        if item is None:
            raise base_exceptions.NotFound
        return item


class ListMixin(BaseService[T]):
    """Mixin class for all() operation."""

    async def all(self) -> PaginatedResponse[T] | list[T]:
        """Returns list of all records."""
        query = select(inspect(self.model).c)
        if self._paginator:
            result = await self._paginator.get_paginated_response(query)
            return result

        result = await self.session.execute(query)
        return result.fetchall()


class CreateServiceMixin(BaseService[T]):
    """Mixin class for create() operation."""

    async def create(self, schema: dict[str, Any]) -> T:
        """Creates and returns item."""
        item = self.model(**schema)
        self.session.add(item)
        await self.session.commit()
        return item


class UpdateServiceMixin(BaseService[T]):
    """Mixin with update() operation."""

    async def update(self, pk: Any, schema: Mapping[str, Any]) -> T:
        """Updates and returns updated item."""
        filtered_schema = {k: v for k, v in schema.items() if v is not None}
        query = (
            update(self.model)
            .where(self.model.id == pk)
            .values(**filtered_schema)
        )
        await self.session.execute(query)
        await self.session.commit()
        return await self.get_or_404(pk)


class DeleteServiceMixin(BaseService[T]):
    """Mixin with delete() operation."""

    async def delete(self, pk: Any) -> None:
        """Deletes item with given pk."""
        item = await self.get_or_404(pk)
        query = delete(self.model).where(self.model.id == item.id)
        await self.session.execute(query)
        await self.session.commit()


class CreateUpdateDeleteService(
    CreateServiceMixin[T],
    UpdateServiceMixin[T],
    DeleteServiceMixin[T],
    BaseService[T],
):
    """Service with create, update and delete methods."""
