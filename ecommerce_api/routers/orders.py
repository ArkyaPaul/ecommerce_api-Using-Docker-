from fastapi import Request, APIRouter, Depends # type: ignore

from ecommerce_api.schemas import Order, Output, JWTData
from ecommerce_api.dependencies.slack_connection import post_to_slack
from ecommerce_api.sql.operations import OrderOperations, ProductOperations
from ecommerce_api.auth.access import authorize_admin, authorize_token
from ecommerce_api.errors import NotFound, Unauthorized

router = APIRouter(tags=["orders"])


@router.get("/order/add/{product_id}", response_model=Output)
async def add_item(
    request: Request,
    product_id: str,
    data: JWTData = Depends(authorize_token)
):
    """
    Add item to shopping cart
    """
    product = ProductOperations.get_by_id(product_id=product_id)
    if not product:
        raise NotFound(details="Product not found")
    if product.quantity <= 0:
        raise NotFound(details="Product out of stock")
    OrderOperations.add(
        product_id=product_id,
        email=data.email
    )
    return Output(success=True, message="Item added to cart")

@router.get("/order/all", response_model=Output)
async def getAll(request: Request, data: JWTData = Depends(authorize_admin)):
    """
    Get all orders
    """
    orders = OrderOperations.get_all(isEmail=False)
    if not orders:
        raise NotFound(details="Order ID not found")
    results = [{
        column.name: getattr(order, column.name)
        for column in order.__table__.columns
    } for order in orders
    ]
    return Output(success=True, results=results)

@router.get("/order/{order_id}", response_model=Output)
async def get(
        request: Request,
        order_id: str, data:
        JWTData = Depends(authorize_admin)
):
    """
    Get order from order_id
    """
    order = OrderOperations.get(order_id=order_id)
    if not order:
        raise NotFound(details="Order ID not found")

    results = {
        column.name: getattr(order, column.name)
        for column in order.__table__.columns
    }
    return Output(success=True, results=results)

@router.get("/order", response_model=Output)
async def get_all_items(
    request: Request,
    email: str,
    data: JWTData = Depends(authorize_token)
):
    """
    Returns all items in user's shopping cart
    """
    if data.user_type=='customer' and data.email!=email:
        raise Unauthorized(details="You are not authorized to view this order")
    items = OrderOperations.get_all(isEmail=True, email=email)
    serialized_items = [
        Order.model_validate(item).model_dump()
        for item in items
    ]
    return Output(success=True, results=serialized_items)


@router.delete("/order/remove/{product_id}", response_model=Output)
async def remove_item(
    request: Request,
    product_id: str,
    data: JWTData = Depends(authorize_token)
):
    """
    Removes item from cart
    """
    OrderOperations.remove_item(email=data.email, product_id=product_id)
    return Output(success=True, message="Item deleted from cart")


@router.post("/order/cancel/{order_id}", response_model=Output)
async def cancel_order(
    request: Request,
    order_id: str,
    data: JWTData = Depends(authorize_token)
):
    """
    Cancel order
    """
    OrderOperations.cancel(order_id=order_id, email=data.email)
    return Output(success=True, message="Order cancelled")


@router.post("/order/submit", response_model=Output)
async def submit_order(
    request: Request,
    payment_type: str,
    data: JWTData = Depends(authorize_token)
):
    """
    Submit new order
    """
    order_id = OrderOperations.get_order_id_from_email(email=data.email)
    order = OrderOperations.submit(order_id=order_id, payment_type=payment_type)
    await post_to_slack(order=order)
    order_data = {
        column.name: getattr(order, column.name)
        for column in order.__table__.columns
    }
    return Output(success=True, results=order_data)












