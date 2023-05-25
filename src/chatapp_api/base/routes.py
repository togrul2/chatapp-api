from typing import Any

from fastapi import status

from src.chatapp_api.base.schemas import DetailMessage

RouteResponse = dict[int | str, dict[str, Any]]

BadDataResponse: RouteResponse = {
    status.HTTP_400_BAD_REQUEST: {
        "model": DetailMessage,
        "description": "Invalid body.",
    }
}

BadCredentialsResponse: RouteResponse = {
    status.HTTP_401_UNAUTHORIZED: {
        "model": DetailMessage,
        "description": "Bad access token.",
    }
}

NotFoundResponse: RouteResponse = {
    status.HTTP_404_NOT_FOUND: {
        "model": DetailMessage,
        "description": "Not found.",
    }
}
