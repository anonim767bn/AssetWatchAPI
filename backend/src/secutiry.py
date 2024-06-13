from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import JWTError, jwt
from src.config import settings
from src.db import user_operations, DB
from src.models import User
from typing import Optional


class Authentication:
    """
    A class used to handle user authentication.

    ...

    Attributes
    ----------
    pwd_context : CryptContext
        an instance of CryptContext for password hashing and verification

    Methods
    -------
    verify_password(plain_password: str, hashed_password: str) -> bool:
        Verifies if the plain password matches the hashed password.
    get_password_hash(password: str) -> str:
        Returns the hashed version of the provided password.
    generate_JWT_token(username: str, encode_data: Optional[Dict[str, Any]] = {}, expires_timedelta: timedelta = None) -> str:
        Generates a JWT token with the provided data.
    authenticate_user(username: str, password: str) -> User:
        Authenticates the user with the provided username and password.
    get_username_by_token(token: str) -> str | None:
        Returns the username associated with the provided token.
    """
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """ Compare plain password with hashed password

        Args:
            plain_password (str): Plain text password
            hashed_password (str): Hashed password

        Returns:
            bool: True if plain_password hash matches with hashed_password else False
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """Get password hash

        Args:
            password (str): Password or any string who need to hash

        Returns:
            str: Hashed password
        """
        return self.pwd_context.hash(password)

    def generate_JWT_token(self, username: str, encode_data: Optional[dict] = {}, expires_timedelta: timedelta = None) -> str:
        """Generate JWT token

        Args:
            username (str): Username of the user. Encoden in the token as 'sub'
            encode_data (Dict[str, Any]): Any data to encode in the token
            expires_timedelta (timedelta, optional): Token lifetime. Defaults in config. 

        Returns:
            str: JWT token
        
        Raises:
            ValueError: If encode_data is not a dictionary
        """
        if not isinstance(encode_data, dict):
            raise ValueError("encode_data must be a dictionary")

        to_encode = encode_data.copy()
        if not expires_timedelta:
            expires_timedelta = timedelta(
                minutes=settings.TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_timedelta
        to_encode.update({"exp": expire, "sub": username})
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

    async def get_username_by_token(self, token: str) -> str | None:
        """
        Get the username of the user by the JWT token.
        Args:
            token (str): JWT token

        Returns:
            str | None: string of the username or None if the token is invalid or expired
        """
        try:
            payload = jwt.decode(token, settings.TOKEN_SECRET,
                                 algorithms=[settings.ALGORITHM])
            user = payload['sub']
            return user
        except JWTError as e:
            return None


auth = Authentication()