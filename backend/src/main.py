from fastapi import FastAPI, Response, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.router import router, user_routes
from src.db import user_operations, DB
from src.config import settings
from src.schemas import *
from src.secutiry import auth



app = FastAPI()

origins = [
    "http://10.82.104.247:5173",
    "http://localhost:5173",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)
app.include_router(user_routes)


scheduler = AsyncIOScheduler()
scheduler.start()
scheduler.add_job(
    DB.update_price_histories, 
    'interval', 
    minutes=settings.DB_UPDATE_INTERVAL_MINUTES
)


@app.get('/')
def read_item():
    return '<Hello world>'


@app.post('/token')
async def login_for_access_token(form_data: UserCreateOrLogin):
    try:
        user = await auth.authenticate_user(form_data.username, form_data.password)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    return {
        'token': auth.generate_JWT_token(username=user.username), 
        'token_type': 'bearer'
    }


@app.post('/register')
async def register(form_data: UserCreateOrLogin):
    print(form_data)
    user = user_operations.get_user_by_username_from_db(form_data.username)
    if user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail='User already exists'
        )
    user = user_operations.create_user(
        username=form_data.username,
        hashed_password=auth.get_password_hash(form_data.password)
    )
    return Response(status_code=status.HTTP_201_CREATED, content='User created')


