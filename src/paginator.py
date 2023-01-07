"""Module with custom paginator classes."""
from sqlalchemy.orm import Query as SQLQuery
from fastapi import Query

import config


def pagination(page: int = Query(), page_size: int = Query(default=config.PAGE_SIZE_DEFAULT)):
    """Dependency for pagination"""

    ...


class LimitOffsetPaginator:
    """Paginator class based on limit & offset queries."""

    def paginate(self, query: SQLQuery):
        ...
