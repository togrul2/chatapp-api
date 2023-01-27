"""Main module where fastapi app is being run from."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from src.config import STATIC_ROOT, STATIC_URL
from src.db import broadcaster, ping_redis_database, ping_sql_database
from src.routes.chat import router as chat_router
from src.routes.friendship import router as friendship_router
from src.routes.user import router as user_router

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
    on_startup=[ping_sql_database, ping_redis_database, broadcaster.connect],
    on_shutdown=[broadcaster.disconnect],
)

app.mount(
    STATIC_URL,
    StaticFiles(directory=STATIC_ROOT),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
app.include_router(friendship_router)
app.include_router(chat_router)
