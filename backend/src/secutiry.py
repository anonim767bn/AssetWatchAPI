"""This module contains the Authentication class for handling user authentication."""

from datetime import datetime, timedelta
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from src.config import settings
from src.db import user_operations
from src.models import User


class Authentication:
    """A class used to handle user authentication."""

    def __init__(self):
        """
        Initialize an instance of the Authentication class.

        The instance is initialized with a CryptContext for password hashing and verification.
        """
        self.pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Compare plain password with hashed password.

        Args:
            plain_password (str): Plain text password
            hashed_password (str): Hashed password

        Returns:
            bool: True if plain_password hash matches with hashed_password else False
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Get password hash.

        Args:
            password (str): Password or any string who need to hash

        Returns:
            str: Hashed password
        """
        return self.pwd_context.hash(password)

    def generate_jwt_token(
        self,
        username: str,
        encode_data: Optional[dict] = None,
        expires_timedelta: Optional[timedelta] = None,
    ) -> str:
        """Generate JWT token.

        Args:
            username (str): Username of the user. Encoded in the token as 'sub'.
            encode_data (Dict[str, Any], optional): Any data to encode in the token. Defaults to None.
            expires_timedelta (timedelta, optional): Token lifetime. Defaults in config.

        Returns:
            str: JWT token.

        Raises:
            ValueError: If encode_data is not a dictionary.
        """
        if encode_data is None:
            encode_data = {}
        if not isinstance(encode_data, dict):
            raise ValueError('encode_data must be a dictionary')

        to_encode = encode_data.copy()
        if not expires_timedelta:
            expires_timedelta = timedelta(
                minutes=settings.TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_timedelta
        to_encode.update({'exp': expire, 'sub': username})
        return jwt.encode(to_encode, settings.TOKEN_SECRET, algorithm=settings.ALGORITHM)

    async def authenticate_user(self, username: str, password: str) -> User:
        """
        Authenticate the user with the given username and password.

        Args:
            username (str): username of the user
            password (str): password of the user

        Raises:
            Exception: if the username or password is incorrect or the user is not found

        Returns:
            User: object of the user
        """
        user: User = user_operations.get_user_by_username_from_db(username)
        if not user:
            raise Exception(f'User with username {username} not found')
        if not self.verify_password(password, user.hash_password):
            raise Exception('Incorrect password')
        return user

    async def get_username_by_token(self, token: str) -> Optional[str]:
        """
        Get the username of the user by the JWT token.

        Args:
            token (str): JWT token

        Returns:
            Optional[str]: string of the username or None if the token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.TOKEN_SECRET, algorithms=[settings.ALGORITHM])
        except JWTError:
            return None

        return payload.get('sub', None)


auth = Authentication()
