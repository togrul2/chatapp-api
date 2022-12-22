from functools import partial

from models import Chat
from services.base import get_service, CreateUpdateDeleteService


class ChatService(CreateUpdateDeleteService):
    model = Chat


get_chat_service = partial(get_service, ChatService)
