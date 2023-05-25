"""Module with user repository"""
from dataclasses import dataclass

from sqlalchemy import and_, exists, func, or_, select

from src.chatapp_api.base.repository import BaseRepository
from src.chatapp_api.paginator import BasePaginator, Page
from src.chatapp_api.user.models import User


@dataclass
class UserRepository(BaseRepository[User]):
    """User repository with"""

    paginator: BasePaginator

    async def is_username_taken(self, username: str) -> bool:
        """Returns whether there is a user with given username"""
        return (
            await self.session.scalar(
                exists().where(User.username == username).select()
            )
        ) or False

    async def is_username_taken_not_by(self, username: str, id: int) -> bool:
        """Returns whether there is a user with given username.
        Excludes given user id from search."""
        return (
            await self.session.scalar(
                exists()
                .where(and_(User.username == username, User.id != id))
                .select()
            )
        ) or False

    async def is_email_taken(self, email: str) -> bool:
        """Returns whether there is a user with given email."""
        return (
            await self.session.scalar(
                exists().where(User.email == email).select()
            )
        ) or False

    async def is_email_taken_not_by(self, email: str, id: int) -> bool:
        """Returns whether there is a user with given email.
        Excludes given user id from search."""
        return (
            await self.session.scalar(
                exists()
                .where(and_(User.email == email, User.id != id))
                .select()
            )
        ) or False

    async def find_by_id(self, id: int) -> User | None:
        """Returns user with given id or none if not found."""
        return await self.session.get(User, id)

    async def find_by_username(self, username: str) -> User | None:
        """Returns user with given username"""
        return await self.session.scalar(
            select(User).where(User.username == username)
        )

    async def find_users(self) -> Page[User]:
        """Returns all users for given page"""
        return await self.paginator.get_page_for_model(select(User))

    async def find_users_matching_keyword(self, keyword: str) -> Page[User]:
        """Returns all users for given page which match given keyword."""
        return await self.paginator.get_page_for_model(
            select(User).where(
                or_(
                    func.upper(User.username).like(f"%{keyword}%"),
                    User.email.like(f"%{keyword}%"),
                )
            )
        )
