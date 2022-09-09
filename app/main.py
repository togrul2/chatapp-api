from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import BASE_DIR
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
    }
)

app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"),
          name="static")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(user_router)
