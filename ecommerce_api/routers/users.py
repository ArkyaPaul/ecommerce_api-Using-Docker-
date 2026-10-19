from fastapi import APIRouter, Request, Depends # type: ignore
from fastapi.encoders import jsonable_encoder # type: ignore
from ecommerce_api.schemas import Output, JWTData
from ecommerce_api.errors import NotFound
from ecommerce_api.sql.operations import UserOperations

from ecommerce_api.auth.access import authorize_admin

router = APIRouter(tags=["users"])


@router.get("/users/all", response_model=Output)
async def all_users(
    request: Request,
    data: JWTData = Depends(authorize_admin)
):
    """
    Returns a list of all signed-up users
    """
    users = UserOperations.get_all()
    if not users:
        raise NotFound(details="No users found")
    return Output(success=True,results=jsonable_encoder(users))


@router.get("/users/{email}", response_model=Output)
async def get_user(
    request: Request,
    email: str,
    data: JWTData = Depends(authorize_admin)
):
    """
    Returns user info from database
    """
    user = UserOperations.get_by_email(email=email)
    if not user:
        raise NotFound(details="User not found")
    user_data = {
        column.name: getattr(user, column.name)
        for column in user.__table__.columns
    }
    return Output(success=True, results=user_data)


@router.delete("/users/{email}", response_model=Output)
async def delete_user(
    request: Request,
    email: str,
    data: JWTData = Depends(authorize_admin)
):
    """
    Returns user info from database
    """
    user = UserOperations.get_by_email(email=email)
    if not user:
        raise NotFound(details="User not found")
    UserOperations.delete(email=email)
    return Output(success=True, message="User deleted")