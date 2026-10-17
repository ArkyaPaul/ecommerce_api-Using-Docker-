from datetime import datetime, timedelta, timezone

from jose import ExpiredSignatureError, JWTError, jwt # type: ignore
from fastapi.security import OAuth2PasswordBearer # type: ignore
from fastapi import Depends # type: ignore
from functools import wraps # type: ignore

from ecommerce_api.schemas import JWTData, User
from ecommerce_api.enums import UserType
from ecommerce_api.errors import Forbidden, Unauthorized
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
    payload.update({"exp": datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),"type": "refresh",})
    
    refresh_jwt = jwt.encode( claims=payload, key=JWT_SECRET_KEY, algorithm=ALGORITHM)
    return refresh_jwt


def authorize_token(
    token: str = Depends(oauth2_scheme),
    adminAccess: bool = False
) -> JWTData:
    """Decode and validate an access token."""
    try:
        payload = jwt.decode(
            token=token,
            key=JWT_SECRET_KEY,
            algorithms=[ALGORITHM],
            options={"verify_exp": True},
        )

        if payload.get("type") != "access":
            raise Unauthorized(details="Invalid access token")

        if not payload.get("email"):
            raise Unauthorized(details="Could not validate credentials")

        if adminAccess and payload.get("user_type") != 'admin':
            raise Forbidden()

        return JWTData(**payload)

    except ExpiredSignatureError:
        raise Unauthorized(details="Access token has expired")
    except JWTError:
        raise Unauthorized(details="Could not validate credentials")

def authorize_admin(
    token: str = Depends(oauth2_scheme),
) -> JWTData:
    return authorize_token(token=token, adminAccess=True)
