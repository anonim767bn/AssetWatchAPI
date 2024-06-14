"""This module contains the main application and its routes."""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from src.config import settings
from src.db import DB, user_operations
from src.router import router, user_routes
from src.schemas import UserCreateOrLogin
from src.secutiry import auth

app = FastAPI()

origins = [
    'http://10.82.104.247:5173',
    'http://localhost:5173',
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(router)
app.include_router(user_routes)

scheduler = AsyncIOScheduler()
scheduler.start()
scheduler.add_job(
    DB.update_price_histories,
    'interval',
    minutes=settings.DB_UPDATE_INTERVAL_MINUTES,
)


@app.get('/')
def read_item():
    """Endpoint to return a simple greeting.

    Returns:
        str: A greeting message.
    """
    return '<Hello world>'


@app.post('/token')
async def login_for_access_token(form_data: UserCreateOrLogin):
    """Endpoint to authenticate a user and return a JWT token.

    Args:
        form_data (UserCreateOrLogin): The user's login information.

    Returns:
        dict: A dictionary containing the JWT token and its type.

    Raises:
        HTTPException: If authentication fails.
    """
    try:
        user = await auth.authenticate_user(form_data.username, form_data.password)
    except Exception as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        )
    return {
        'token': auth.generate_jwt_token(username=user.username),
        'token_type': 'bearer',
    }


@app.post('/register')
async def register(form_data: UserCreateOrLogin):
    """Endpoint to register a new user.

    Args:
        form_data (UserCreateOrLogin): The user's registration information.

    Returns:
        Response: An HTTP response indicating the result of the registration.

    Raises:
        HTTPException: If the username is already taken.
    """
    print(form_data)
    user = user_operations.get_user_by_username_from_db(form_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User already exists',
        )
    user = user_operations.create_user(
        username=form_data.username,
        hashed_password=auth.get_password_hash(form_data.password),
    )
    return Response(status_code=status.HTTP_201_CREATED, content='User created')
