"""This module contains Pydantic models for User and Asset entities."""

from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


class UserCreateOrLogin(BaseModel):
    """
    Pydantic model for User creation or login.

    Attributes:
        username (str): The username of the User.
        password (str): The password of the User.
    """

    username: str
    password: str


class AssetCreate(BaseModel):
    """
    Pydantic model for Asset creation.

    Attributes:
        currency (str): The currency of the Asset.
        amount (float): The amount of the Asset.
    """

    currency: str
    amount: float


# OAuth2 scheme with the token URL set to "/token"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/token')