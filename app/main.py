from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from starlette.middleware.cors import CORSMiddleware

from db import SessionLocal
from jwt import (create_refresh_token,
                 create_access_token,
                 get_current_user_id,
                 CredentialsException,
                 verify_refresh)
from schemas import UserCreate, UserBase, TokenData, RefreshData
from services import UserService

app = FastAPI()

origins = [
    "http://localhost:8000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/token", status_code=status.HTTP_201_CREATED,
          response_model=TokenData)
async def token(db: Session = Depends(get_db),
                credentials: OAuth2PasswordRequestForm = Depends()):
    """
    Creates access and refresh token for user:
    - **username**: username of a user.
    - **password**: password of a user.
    \f
    Parameters:
        credentials: User's credentials.
        db: session for IO operations with database.
    """
    user_service = UserService(db)
    user = user_service.authenticate_user(credentials.username,
                                          credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password"
        )

    return {
        "access_token": create_access_token(user.id),
        "refresh_token": create_refresh_token(user.id)
    }


@app.post("/api/refresh", status_code=status.HTTP_201_CREATED,
          response_model=TokenData)
async def refresh(data: RefreshData, db: Session = Depends(get_db)):
    """
    Creates access & refresh tokens based on refresh token.
    - **refresh_token**: refresh token
    \f
    Parameters:
        data: refresh_token of a user.
        db: session for IO operations with database.
    """
    user_id = verify_refresh(data.refresh)
    user_service = UserService(db)
    if user_service.get_by_pk(user_id) is None:
        raise CredentialsException

    return {
        "access": create_access_token(user_id),
        "refresh": create_refresh_token(user_id)
    }


@app.post("/api/register", status_code=status.HTTP_201_CREATED,
          response_model=UserBase)
async def register(data: UserCreate, db: Session = Depends(get_db)):
    """
    Create a user in database with given data:
    - **username**: unique name
    - **email**: unique email address
    - **first_name**: first name of a user
    - **last_name**: last name of a user
    - **password**: password
    \f

    Parameters:
        data: User input.
        db: session for IO operations with database.
    """
    user_service = UserService(db)
    if user_service.get_by_username(data.username) is not None:
        raise HTTPException(
            status_code=400,
            detail="User with given username already exists."

        )

    if user_service.get_by_email(data.email) is not None:
        raise HTTPException(
            status_code=400,
            detail="User with given username already exists."
        )

    user = user_service.create(data)
    return user


@app.get("/api/users/me", response_model=UserBase)
async def get_auth_user(user_id: int = Depends(get_current_user_id),
                        db: Session = Depends(get_db)):
    user_service = UserService(db)
    print(user_id)
    user = user_service.get_by_pk(user_id)
    return user


@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    pass
