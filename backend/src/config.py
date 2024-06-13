from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    CMC_API_KEY: str
    DATABASE_URL: str = "sqlite:///./test.db"
    DB_UPDATE_INTERVAL_MINUTES: int = 5
    TOKEN_SECRET: str
    TOKEN_EXPIRE_MINUTES: int = 30 * 60 * 7
    ALGORITHM: str = "HS256"
    BASE_API_URL: str = 'https://pro-api.coinmarketcap.com'
    API_AUTHORIZATION_HEADER: str = 'X-CMC_PRO_API_KEY'

    model_config = SettingsConfigDict(env_file=".env")


settings=Settings()