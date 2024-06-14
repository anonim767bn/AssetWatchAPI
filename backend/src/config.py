"""
This module contains the Settings class which is used to manage the settings for the application.

It uses the BaseSettings class from pydantic_settings and SettingsConfigDict for environment variable configuration.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict

THIRTY = 30
SIXTY = 60
SEVEN = 7
FIVE = 1


class Settings(BaseSettings):
    """
    This class is used to manage the settings for the application.

    It uses the BaseSettings class from pydantic_settings and
    SettingsConfigDict for environment variable configuration.
    """

    CMC_API_KEY: str
    DATABASE_URL: str = 'sqlite:///./test.db'
    DB_UPDATE_INTERVAL_MINUTES: int = FIVE
    TOKEN_SECRET: str
    TOKEN_EXPIRE_MINUTES: int = THIRTY * SIXTY * SEVEN
    ALGORITHM: str = 'HS256'
    BASE_API_URL: str = 'https://pro-api.coinmarketcap.com'
    API_AUTHORIZATION_HEADER: str = 'X-CMC_PRO_API_KEY'

    model_config = SettingsConfigDict(env_file='.env')


settings = Settings()
