from dataclasses import dataclass
from datetime import datetime, timezone

from chatapp_api_hex.domain.entities.user import User
from chatapp_api_hex.domain.events.user_events import UserCreated
from chatapp_api_hex.domain.ports.security import PasswordHasher
from chatapp_api_hex.domain.services.base import DomainService
from chatapp_api_hex.domain.value_objects.email import Email


@dataclass
class UserService(DomainService[User]):
    """Service for handling user-related business logic."""

    password_hasher: PasswordHasher

    def __post_init__(self) -> None:
        self._events: list[UserCreated] = []

    @property
    def events(self) -> list[UserCreated]:
        """Get list of domain events."""
        return self._events

    async def _validate_user_creation(self, username: str, email: str) -> None:
        async with self.unit_of_work as uow:
            errors = {}
            if await uow.user_repository.exists_by_email(email):
                errors["email"] = ["User with this email already exists"]
            if await uow.user_repository.exists_by_username(username):
                errors["username"] = ["User with this username already exists"]

            if errors:
                raise ValueError(errors)

    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        first_name: str | None = None,
        last_name: str | None = None,
        profile_picture: str | None = None,
    ) -> User:
        """Create a new user."""
        async with self.unit_of_work as uow:
            await self._validate_user_creation(username, email)

            hashed_password = self.password_hasher.hash(password)
            user = User(
                id=None,
                username=username,
                email=Email(email),
                password=hashed_password,
                first_name=first_name,
                last_name=last_name,
                profile_picture=profile_picture,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc),
            )

            created_user = await uow.user_repository.create(user)

            self._events.append(
                UserCreated(
                    user_id=created_user.id,
                    username=created_user.username,
                    email=str(created_user.email),
                )
            )

            return created_user

    async def get_user_by_id(self, user_id: int) -> User | None:
        """Get user by ID."""
        async with self.unit_of_work as uow:
            return await uow.user_repository.get_by_id(user_id)

    async def get_user_by_email(self, email: str) -> User | None:
        """Get user by email."""
        async with self.unit_of_work as uow:
            return await uow.user_repository.get_by_email(email)

    async def get_user_by_username(self, username: str) -> User | None:
        """Get user by username."""
        async with self.unit_of_work as uow:
            return await uow.user_repository.get_by_username(username)

    async def update_user_profile(
        self,
        user_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        profile_picture: str | None = None,
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
