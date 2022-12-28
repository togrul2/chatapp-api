from functools import partial

from models import Chat
from services.base import CreateUpdateDeleteService, get_service


class ChatService(CreateUpdateDeleteService):
    model = Chat


get_chat_service = partial(get_service, ChatService)
