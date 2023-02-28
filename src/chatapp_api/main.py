"""Main module where fastapi app is being run from."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.chatapp_api.auth.routes import router as auth_router
from src.chatapp_api.chat.routes import router as chat_router
from src.chatapp_api.config import STATIC_ROOT, STATIC_URL, settings
from src.chatapp_api.db import ping_redis_database, ping_sql_database
from src.chatapp_api.friendship.routes import router as friendship_router
from src.chatapp_api.user.routes import router as user_router

app = FastAPI(
    title="Chatapp API",
    description="""
    Chatapp API

    API for real time communication with friends.
    Chat in private or in public groups.
    """,
    version="0.0.1 beta",
    contact={
        "name": "Togrul Asadov",
        "github": "https://github.com/togrul2",
    },
    on_startup=[ping_sql_database, ping_redis_database],
)

app.mount(
    STATIC_URL,
    StaticFiles(directory=STATIC_ROOT),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=settings.allowed_methods,
    allow_headers=settings.allowed_headers,
)

# Routes
app.include_router(auth_router)
app.include_router(user_router)
app.include_router(friendship_router)
app.include_router(chat_router)
