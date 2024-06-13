from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel


class UserCreateOrLogin(BaseModel):
    username: str
    password: str

class AssetCreate(BaseModel):
    currency: str
    amount: float

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")