from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt # type: ignore
from fastapi.security import OAuth2PasswordBearer # type: ignore
from fastapi import Depends # type: ignore
from functools import wraps # type: ignore

from ecommerce_api.schemas import JWTData, User
from ecommerce_api.enums import UserType
from ecommerce_api.errors import Unauthorized
from ecommerce_api.settings import ACCESS_TOKEN_EXPIRE_MINUTES, JWT_SECRET_KEY, ALGORITHM

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")
REFRESH_TOKEN_EXPIRE_DAYS = 7


def create_access_token(user: User) -> str:
    """
    Create JSON web token, returns signed JWT string
    """
    jwt_data = JWTData(email=user.email, user_type=user.type)
    payload = jwt_data.model_dump()
    payload.update({"exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES), "type": "access",})

    access_jwt = jwt.encode( claims=payload, key=JWT_SECRET_KEY, algorithm=ALGORITHM)
    return access_jwt

def create_refresh_token(user: User) -> str:
    jwt_data = JWTData(email=user.email, user_type=user.type)
    payload = jwt_data.model_dump()
    payload.update({"exp": datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),"type": "refresh",})
    
    refresh_jwt = jwt.encode( claims=payload, key=JWT_SECRET_KEY, algorithm=ALGORITHM)
    return refresh_jwt

def authorize_token(token: str = Depends(oauth2_scheme)) -> JWTData:
    """
    Decodes and verifies access token
    """
    try:
        payload = jwt.decode(
            token=token,
            key=JWT_SECRET_KEY,
            algorithms=ALGORITHM
        )
        if not payload:
            raise Unauthorized(details="Could not validate credentials")
        jwt_data = JWTData(**payload)
    except JWTError:
        raise Unauthorized(details="Could not validate credentials")
    return jwt_data


def admin_access_only(func):
    @wraps(func)
    async def _admin_access_only(*args, **kwargs):
        user_type = kwargs["data"].user_type
        if user_type == UserType.ADMIN:
            return await func(*args, **kwargs)
        raise Unauthorized(details="No access")
    return _admin_access_only

