"""User service module."""
import os
from dataclasses import dataclass

from fastapi import UploadFile

from src.chatapp_api.auth.exceptions import BadTokenException
from src.chatapp_api.auth.jwt import password_context
from src.chatapp_api.base.exceptions import NotFoundException
from src.chatapp_api.paginator import Page
from src.chatapp_api.user.exceptions import (
    EmailAlreadyTaken,
    InvalidOldPassword,
    UsernameAlreadyTaken,
)
from src.chatapp_api.user.models import User
from src.chatapp_api.user.repository import UserRepository


@dataclass
class UserService:
    """User service class.
    Contains methods for performing business logic related to user."""

    user_repository: UserRepository

    @staticmethod
    def get_profile_pictures_dir(user_id: int) -> str:
        """Generates path for user profile picture."""
        return f"users/{user_id}/pfp/"

    @classmethod
    def get_profile_picture_uri(cls, user_id: int, image: UploadFile) -> str:
        """Returns URI for given profile picture."""
        return os.path.join(
            cls.get_profile_pictures_dir(user_id), image.filename
        )

    async def get_by_username(self, username: str) -> User | None:
        """Returns user with matching username."""
        return await self.user_repository.find_by_username(username)

    async def get_or_401(self, id: int) -> User:
        """Returns user with given id.
        If not found, raises 401 unauthenticated error."""
        if (user := await self.user_repository.find_by_id(id)) is None:
            raise BadTokenException

        return user

    async def get_or_404(self, id: int) -> User:
        """Returns user with given id.
        If user with given id does not exist, raises 404 Not Found"""
        if (user := await self.user_repository.find_by_id(id)) is None:
            raise NotFoundException("User with given id has not been found.")

        return user

    async def get_by_username_or_404(self, username: str) -> User:
        """Returns user by his username.
        If user is not found, raises 404 not found error"""
        if (
            user := await self.user_repository.find_by_username(username)
        ) is None:
            raise NotFoundException(
                "User with given username has not been found."
            )

        return user

    async def create_user(
        self,
        username: str,
        email: str,
        first_name: str | None,
        last_name: str | None,
        password: str,
    ) -> User:
        """Creates user with hashed password."""
        if await self.user_repository.exists_user_with_username(username):
            raise UsernameAlreadyTaken

        if await self.user_repository.exists_user_with_email(email):
            raise EmailAlreadyTaken

        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password=password_context.hash(password),
        )
        self.user_repository.add(user)
        await self.user_repository.commit()
        return user

    async def list_users(self, keyword: str | None = None) -> Page:
        """Returns list of items matching the given keyword.
        For now, it is simple exact match."""
        if keyword:
            return await self.user_repository.find_users_matching_keyword(
                keyword
            )

        return await self.user_repository.find_users()

    async def update_profile_picture(
        self, user_id: int, image_url: str
    ) -> User:
        """
        Sets image as a profile picture of a user
        and returns updated user info.
        """
        user = await self.get_or_404(user_id)
        user.profile_picture = image_url
        self.user_repository.add(user)
        await self.user_repository.commit()
        await self.user_repository.refresh(user)
        return user

    async def remove_profile_picture(self, id: int) -> User:
        """
        Sets user's profile picture to null and returns updated info.
        It doesn't delete file from storage.
        """
        user = await self.get_or_404(id)
        user.profile_picture = None
        await self.user_repository.commit()
        await self.user_repository.refresh(user)
        return user

    async def update_user(
        self,
        user_id: int,
        username: str | None,
        email: str | None,
        first_name: str | None,
        last_name: str | None,
    ) -> User:
        """
        Updates user with given user_id
        Validate uniqueness of username and email,
        if they are not met, these validation methods will raise exceptions
        """

        if await self.user_repository.exists_user_with_username_and_id_not(
            username or "", user_id
        ):
            raise UsernameAlreadyTaken

        if await self.user_repository.exists_user_with_email_and_id_not(
            email or "", user_id
        ):
            raise UsernameAlreadyTaken

        user = await self.get_or_404(user_id)

        user.username = username or user.username
        user.email = email or user.email
        user.first_name = first_name or user.first_name
        user.last_name = last_name or user.last_name
        self.user_repository.add(user)
        await self.user_repository.commit()
        await self.user_repository.refresh(user)
        return user

    async def update_user_password(
        self, user_id: int, old_password: str, new_password: str
    ) -> User:
        """Updates user's password. If old one is incorrect raises 400 error"""
        user = await self.get_or_401(user_id)

        if not password_context.verify(old_password, user.password):
            raise InvalidOldPassword

        user.password = password_context.hash(new_password)
        self.user_repository.add(user)
        await self.user_repository.commit()
        return user

    async def delete_user(self, id: int) -> None:
        """Deletes user with given id.
        If user is not found, raises 401 not authenticated."""
        user = await self.get_or_404(id)
        await self.user_repository.delete(user)
        await self.user_repository.commit()
