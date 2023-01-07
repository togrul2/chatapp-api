"""Main module where fastapi app is being run from."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import BASE_DIR, STATIC_URL
from routes.chat import router as chat_router
from routes.friendship import router as friendship_router
from routes.user import router as user_router

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
)

app.mount(
    STATIC_URL,
    StaticFiles(directory=BASE_DIR / "static"),
    name="static",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def ping_sql_database():
    ...


@app.on_event("startup")
def ping_redis_db():
    ...


app.include_router(user_router)
app.include_router(friendship_router)
app.include_router(chat_router)
