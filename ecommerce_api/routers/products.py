from fastapi import APIRouter, Request, Depends # type: ignore

from ecommerce_api.schemas import Output, Product, JWTData
from ecommerce_api.enums import ProductCategory
from ecommerce_api.errors import NotFound
from ecommerce_api.sql.operations import ProductOperations
from ecommerce_api.auth.access import authorize_admin, authorize_token

router = APIRouter(
    tags=["products"]
)


@router.get("/products/all", response_model=Output)
async def get_all(
    request: Request,
    data: JWTData = Depends(authorize_token)
):
    """
    Get a list of all products
    """
    products = ProductOperations.get_all()
    if not products:
        raise NotFound(details="No products found")
    all_products = [
        {
            column.name: getattr(product, column.name)
            for column in product.__table__.columns
        }
        for product in products
    ]
    return Output(success=True, results=all_products)


@router.get("/products/{product_id}", response_model=Output)
async def get_by_id(
    request: Request,
    product_id: str,
    data: JWTData = Depends(authorize_token)
):
    """
     Return a product by a primary key
    """
    products = ProductOperations.get_by_id(product_id=product_id)
    if not products:
        raise NotFound(details=f"Product with ID {product_id} not found")
    specific_product = {
        column.name: getattr(products, column.name)
        for column in products.__table__.columns
    }
    return Output(success=True, results=specific_product)


@router.get("/products/category/{category}", response_model=Output)
async def get_by_category(
    category: ProductCategory,
    data: JWTData = Depends(authorize_token)
):
    """
    Get all products by category
    """
    products = ProductOperations.get_by_category(category=category)
    if not products:
        raise NotFound(details="No products found in this category")
    matching_products = [
        {
            column.name: getattr(product, column.name)
            for column in product.__table__.columns
        }
        for product in products
    ]
    return Output(success=True, results=matching_products)


@router.post("/products/new", response_model=Output)
async def create_new_product(
    request: Request,
    product: Product,
    data: JWTData = Depends(authorize_admin)
):
    """
    Create new product
    """
    ProductOperations.create(product=product)
    return Output(success=True, results=product)


@router.put("/products/{product_id}", response_model=Output)
async def update_product(
    request: Request,
    product_id: str,
    product: Product,
    data: JWTData = Depends(authorize_admin)
):
    """
    Update existing product
    """
    updated_product = ProductOperations.update(
        product_id=product_id,
        product=product
    )
    return Output(success=True, results=updated_product)


@router.delete("/products/{product_id}", response_model=Output)
async def delete_product(
    request: Request,
    product_id: str,
    data: JWTData = Depends(authorize_admin)
):
    """
    Delete product by product id (primary key)
    """
    product = ProductOperations.get_by_id(product_id=product_id)
    if not product:
        raise NotFound(details="Product not found")
    ProductOperations.remove(product_id=product_id)
    return Output(success=True, message="Product deleted")
