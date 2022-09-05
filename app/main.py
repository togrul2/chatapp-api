from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from db import SessionLocal
from jwt import create_refresh_token, create_access_token, get_current_user
from schemas import UserCreate, UserBase
from services import UserService

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/api/token", status_code=status.HTTP_201_CREATED)
async def login(db: Session = Depends(get_db),
                credentials: OAuth2PasswordRequestForm = Depends()):
    user_service = UserService(db)
    user = user_service.authenticate_user(credentials.username,
                                          credentials.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid username or password"
        )

    return {
        "access": create_access_token(user['id']),
        "refresh": create_refresh_token(user['id'])
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
        db: session for IO operation with database.
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


@app.get("/api/users/me")
async def get_auth_user(user_id: int = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    return {"user": "me"}


@app.get("/api/users/{user_id}")
async def get_user(user_id: int, db: Session = Depends(get_db)):
    pass
