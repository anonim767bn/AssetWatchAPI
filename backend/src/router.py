from fastapi import APIRouter
from src.http_client import cmc_client
from src.db import user_operations, DB, currency_operations, asset_operation
from src.secutiry import auth
from src.models import User
from fastapi import Depends, HTTPException, status
from src.schemas import AssetCreate, oauth2_scheme


router = APIRouter(
    prefix="/cryptocurrencies",
)


@router.get("")
async def get_cryptocurrencies():
    return DB.get_listings_from_db()


@router.get("/{currency_id}")
async def get_cryptocurrency(currency_id: int):
    try:
        return DB.get_listings_from_db()[currency_id-1]
    except IndexError:
        raise HTTPException(status_code=404, detail="Currency not found")


user_routes = APIRouter(
    prefix="/users",
)


async def get_current_active_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    username = await auth.get_username_by_token(token)
    user = user_operations.get_user_by_username_from_db(username)
    if not user:
        raise credentials_exception
    return user


@user_routes.get('/me')
async def read_users_me(current_user: User = Depends(get_current_active_user)):
    user = current_user
    return user.username


@user_routes.get('/me/assets')
async def read_users_assets(current_user: User = Depends(get_current_active_user)):
    return user_operations.get_user_assets_info(current_user)
    

@user_routes.post('/me/assets')
async def create_user_asset(asset_form: AssetCreate, current_user: User = Depends(get_current_active_user)):
    currency = currency_operations.get_currency_by_name_from_db(asset_form.currency)
    if not currency:
        raise HTTPException(status_code=404, detail="Currency not found")
    try:
        asset = user_operations.create_user_asset(current_user, currency)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'create_user_asset {str(e)}')
    try:
        asset_operation.add_asset_amount(asset, asset_form.amount)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f'add asset amount{str(e)}')
    return {'status': 'success'}
