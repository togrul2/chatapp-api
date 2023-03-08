from enum import Enum

from pydantic import BaseModel, ValidationError


def validate_dict(cls: type[BaseModel], instance: dict) -> bool:
    """Validates dictionary against given pydantic model."""
    try:
        cls(**instance)
        return True
    except ValidationError:
        return False


class AssertionErrors(str, Enum):
    """Enum for storing assertion error messages"""

    HTTP_NOT_200_OK = "Response code is not http 200 success ok"
    HTTP_NOT_201_CREATED = "Response code is not http 201 success created"
    HTTP_NOT_204_NO_CONTENT = (
        "Response code is not http 204 success no content"
    )
    HTTP_NOT_401_UNAUTHENTICATED = (
        "Response code is not http 401 error unauthenticated"
    )
    HTTP_NOT_403_FORBIDDEN = "Response code is not http 403 error forbidden"
    HTTP_NOT_409_CONFLICT = "Response code is not http 409 error confict"
    HTTP_NOT_404_NOT_FOUND = "Response code is not http 404 error not found"

    INVALID_BODY = "Invalid response body"
    INVALID_NUM_OF_ROWS = "Unexpected number of rows"
