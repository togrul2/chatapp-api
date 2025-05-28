from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from chatapp_api_hex.domain.ports.unit_of_work import UnitOfWork


@dataclass
class SQLAlchemyUnitOfWork(UnitOfWork):
    """SQLAlchemy implementation of the Unit of Work pattern."""

    session: AsyncSession

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()
