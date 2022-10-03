from functools import partial

from models import Chat
from services.base import BaseService, get_service


class ChatService(BaseService):
    model = Chat


get_chat_service = partial(get_service, ChatService)
