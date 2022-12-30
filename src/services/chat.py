from models.chat import Chat
from services.base import CreateUpdateDeleteService


class ChatService(CreateUpdateDeleteService):
    model = Chat
