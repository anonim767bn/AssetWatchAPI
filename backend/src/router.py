"""This module defines the routes for the FastAPI application."""

from fastapi import APIRouter, Depends, HTTPException, status

from src.db import DB, asset_operation, currency_operations, user_operations
from src.models import User
from src.schemas import AssetCreate, oauth2_scheme
from src.secutiry import auth

HTTP_STATUS_NOT_FOUND = 404
HTTP_STATUS_BAD_REQUEST = 400

router = APIRouter(
    prefix='/cryptocurrencies',
)


@router.get('')
async def get_cryptocurrencies():
    """
    Get a list of all cryptocurrencies.

    Returns:
        list: A list of all cryptocurrencies.
    """
    return DB.get_listings_from_db()


@router.get('/{currency_id}')
async def get_cryptocurrency(currency_id: int):
    """
    Get a specific cryptocurrency by its ID.

    Args:
        currency_id (int): The ID of the cryptocurrency.

    Returns:
        dict: The cryptocurrency with the given ID.

    Raises:
        HTTPException: If the cryptocurrency with the given ID does not exist.
    """
    try:
        return DB.get_listings_from_db()[currency_id-1]
    except IndexError:
        raise HTTPException(status_code=HTTP_STATUS_NOT_FOUND, detail='Currency not found')


user_routes = APIRouter(
    prefix='/users',
)


oauth2_scheme_depends = Depends(oauth2_scheme)


async def get_current_active_user(token: str = oauth2_scheme_depends):
    """
    Get the current active user by their token.

    Args:
        token (str): The token of the user.

    Returns:
        User: The current active user.

    Raises:
        credentials_exception: If the token is invalid.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )
    username = await auth.get_username_by_token(token)
    user = user_operations.get_user_by_username_from_db(username)
    if not user:
        raise credentials_exception
    return user


get_current_active_user_depends = Depends(get_current_active_user)


@user_routes.get('/me')
async def read_users_me(current_user: User = get_current_active_user_depends):
    """
    Get the username of the current active user.

    Args:
        current_user (User): The current active user.

    Returns:
        str: The username of the current active user.
    """
    user = current_user
    return user.username


get_current_active_user_depends = Depends(get_current_active_user)


@user_routes.get('/me/assets')
async def read_users_assets(current_user: User = get_current_active_user_depends):
    """
    Get the assets of the current active user.

    Args:
        current_user (User): The current active user.

    Returns:
        list: The assets of the current active user.
    """
    return user_operations.get_user_assets_info(current_user)


get_current_active_user_depends = Depends(get_current_active_user)


@user_routes.post('/me/assets')
async def create_user_asset(asset_form: AssetCreate, current_user: User = get_current_active_user_depends):
    """
    Create a new asset for the current active user.

    Args:
        asset_form (AssetCreate): The form data to create the asset.
        current_user (User): The current active user.

    Returns:
        dict: A message indicating the success of the operation.

    Raises:
        HTTPException: If the currency does not exist or if there is an error creating the asset.
    """
    currency = currency_operations.get_currency_by_name_from_db(asset_form.currency)
    if not currency:
        raise HTTPException(status_code=HTTP_STATUS_NOT_FOUND, detail='Currency not found')
    try:
        asset = user_operations.create_user_asset(current_user, currency)
        print(asset)
    except Exception as create_error:
        raise HTTPException(status_code=HTTP_STATUS_BAD_REQUEST, detail=f'create_user_asset {str(create_error)}')
    try:
        asset_operation.add_asset_amount(asset.id, asset_form.amount)
    except Exception as add_error:
        raise HTTPException(status_code=HTTP_STATUS_BAD_REQUEST, detail=f'add asset amount{str(add_error)}')
    return {'status': 'success'}
