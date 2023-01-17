"""Module with custom paginator classes."""

import math
from abc import ABC, abstractmethod

from sqlalchemy import func, select
from sqlalchemy.engine import Row
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import Select

from src.models.base import Base
from src.schemas.base import PaginatedResponse


class BasePaginator(ABC):
    """Base class for paginator"""

    def __init__(self, session: AsyncSession, page: int, page_size: int):
        self.session = session
        self.page = page
        self.page_size = page_size
        self.total_count = None
        self.total_pages = None

    @abstractmethod
    async def paginate(self, query: Select) -> Select:
        """Method where pagination takes place."""

    async def _response(
        self, results: list[Base] | list[Row]
    ) -> PaginatedResponse:
        """Returns pydantic response model for paginated queries."""
        return PaginatedResponse.construct(
            results=results,
            total_pages=self.total_pages,
            total_records=self.total_count,
            current_page=self.page,
            items_per_page=self.page_size,
        )

    async def get_paginated_response_for_model(self, query: Select):
        """
        Returns pydantic response with pagination
        applied to query of orm model. Basically
        this method is for cases when scalar() | scalars()
        can be used where select() only takes model instance.

        Example:
            >>> from src.models.user import User
            >>> list_query = select(User)
            >>> response = self.get_paginated_response_for_model(list_query)
        """
        query = await self.paginate(query)
        results = (await self.session.scalars(query)).all()
        return await self._response(results)

    async def get_paginated_response_for_rows(self, query: Select):
        """
        Returns pydantic response with pagination applied to query of Row.
        Basically this method is for cases when scalar() is not used
        and select() takes different fields.

        Example:
            >>> from src.models.chat import Chat, Membership
            >>> list_query = (
            >>>     select(Chat, func.count(Membership.id))
            >>>     .join(Membership).group_by(Chat.id))
            >>> response = self.get_paginated_response_for_rows(list_query)
        """
        query = await self.paginate(query)
        results = (await self.session.execute(query)).all()
        return await self._response(results)


class LimitOffsetPaginator(BasePaginator):
    """Limit offset implementation of pagination.
    Uses database limit & offset query parameters for paginating results."""

    async def paginate(self, query: Select) -> Select:
        offset_size = (self.page - 1) * self.page_size
        total_count_query = select([func.count()]).select_from(query)
        self.total_count = await self.session.scalar(total_count_query)
        self.total_pages = math.ceil(self.total_count / self.page_size)
        return query.offset(offset_size).limit(self.page_size)
