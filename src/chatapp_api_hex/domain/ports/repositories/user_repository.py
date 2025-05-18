from abc import abstractmethod
from typing import Optional

from chatapp_api_hex.domain.entities.user import User
from chatapp_api_hex.domain.ports.repositories.base import Repository


class UserRepository(Repository[User]):
    """Repository interface for User entity."""

    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        pass

    @abstractmethod
    async def get_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        pass

    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """Check if user exists with given email."""
        pass

    @abstractmethod
    async def exists_by_username(self, username: str) -> bool:
        """Check if user exists with given username."""
        pass
