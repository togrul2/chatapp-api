from datetime import datetime, timezone
from typing import Optional

from chatapp_api_hex.domain.entities.user import User
from chatapp_api_hex.domain.events.user_events import UserCreated
from chatapp_api_hex.domain.ports.security import PasswordHasher
from chatapp_api_hex.domain.ports.unit_of_work import UnitOfWork
from chatapp_api_hex.domain.services.base import DomainService
from chatapp_api_hex.domain.value_objects.email import Email


class UserService(DomainService[User]):
    """Service for handling user-related business logic."""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        password_hasher: PasswordHasher,
    ) -> None:
        super().__init__(unit_of_work)
        self._events: list[UserCreated] = []
        self._password_hasher = password_hasher

    @property
    def events(self) -> list[UserCreated]:
        """Get list of domain events."""
        return self._events

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
    ) -> User:
        """Create a new user."""
        async with self.unit_of_work as uow:
            # Check if user with same email or username exists
            if await uow.user_repository.exists_by_email(email):
                raise ValueError("User with this email already exists")
            if await uow.user_repository.exists_by_username(username):
                raise ValueError("User with this username already exists")

            # Create new user
            now = datetime.now(timezone.utc)
            user = User(
                id=None,
                username=username,
                email=Email(email),
                password=password,  # Note: Password should be hashed before this point
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
                created_at=now,
                updated_at=now,
            )

            # Save user
            created_user = await uow.user_repository.create(user)

            # Create and store event
            event = UserCreated(
                user_id=created_user.id,
                username=created_user.username,
                email=str(created_user.email),
            )
            self._events.append(event)

            return created_user

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        async with self.unit_of_work as uow:
            return await uow.user_repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        async with self.unit_of_work as uow:
            return await uow.user_repository.get_by_email(email)

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username."""
        async with self.unit_of_work as uow:
            return await uow.user_repository.get_by_username(username)

    async def update_user_profile(
        self,
        user_id: int,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        profile_picture: Optional[str] = None,
    ) -> User:
        """Update user profile information."""
        async with self.unit_of_work as uow:
            user = await uow.user_repository.get_by_id(user_id)
            if not user:
                raise ValueError(f"User with id {user_id} not found")

            user.update_profile(
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
            )

            return await uow.user_repository.update(user)
