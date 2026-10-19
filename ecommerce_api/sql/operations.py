from operator import and_

from sqlalchemy.orm import Session # type: ignore
from typing import List

from ecommerce_api.sql import models
from ecommerce_api.schemas import User, Product, Order
from ecommerce_api.sql.database import database_operation
from ecommerce_api.errors import NotFound, BadRequest, Unauthorized
from ecommerce_api.enums import OrderStatus
from ecommerce_api.auth.user_pass import to_hash


class UserOperations:
    """
    Database operations on User class (SQL table)
    """

    @staticmethod
    @database_operation
    def create(db: Session, user: User) -> None:
        """Create new user"""
        user.password = to_hash(user.password)
        db.add(models.User(**user.dict()))
        db.commit()

    @staticmethod
    @database_operation
    def get_by_email(db: Session, email: str) -> models.User | None:
        """Get user by email"""
        user = db.query(models.User).filter(
            models.User.email == email
        ).first()
        return user

    @staticmethod
    @database_operation
    def get_all(db: Session) -> List[models.User] | None:
        """Get all users from db"""
        all_users = db.query(models.User).all()
        return all_users

    @staticmethod
    @database_operation
    def delete(db: Session, email: str) -> None:
        """Delete a user"""
        db.query(models.User).filter(models.User.email == email).delete()
        db.commit()


class ProductOperations:
    """
    Database operations on Product class (SQL table)
    """

    @staticmethod
    @database_operation
    def create(db: Session, product: Product) -> None:
        """Create a product"""
        for i in range(product.quantity):
            new_product = models.Product(**product.dict())
            new_product.quantity = 1
            db.add(new_product)
        db.commit()

    @staticmethod
    @database_operation
    def get_all(db: Session) -> List[models.Product] | None:
        all_products = db.query(models.Product).all()
        return all_products

    @staticmethod
    @database_operation
    def get_by_id(
        db: Session,
        product_id: str
    ) -> models.Product | None:
        """Get product by id"""
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()
        return product

    @staticmethod
    @database_operation
    def get_by_category(
        db: Session,
        category: str
    ) -> List[models.Product] | None:
        """Get product by category"""
        matching_products = db.query(models.Product).filter(
            models.Product.category == category
        ).all()
        return matching_products

    @staticmethod
    @database_operation
    def update(
        db: Session,
        product_id: str,
        product: Product
    ) -> models.Product:
        """Update product"""
        updated_product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).update(product.dict(exclude="id"))
        db.commit()
        return updated_product

    @staticmethod
    @database_operation
    def remove(db: Session, product_id: str) -> None:
        """Delete product from db"""
        db.query(models.Product).filter(
            models.Product.id == product_id
        ).delete()
        db.commit()


class OrderOperations:
    """
    Database operations on Order class (SQL table)
    """

    @staticmethod
    @database_operation
    def add(
        db: Session,
        email: str,
        product_id: str
    ) -> None:
        """Add product to cart"""
        active_order = db.query(models.Order).filter(
            models.Order.user_email == email,
            models.Order.status == OrderStatus.IN_PROGRESS
        ).first()
        if not active_order:
            active_order = Order(user_email=email)
            active_order = models.Order(**active_order.dict())
            db.add(active_order)
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()
        product.quantity -= 1
        product.order = active_order
        active_order.total_price += product.price
        db.commit()

    @staticmethod
    @database_operation
    def get(db: Session, order_id: str) -> models.Order:
        """Get order (all items in cart)"""
        order = db.query(models.Order).filter(
            models.Order.id == order_id
        ).first()
        return order

    @staticmethod
    @database_operation
    def get_all(db: Session, isEmail: bool, email: str = None) -> List[models.Order]:
        """Get all orders from db"""
        if not isEmail:
            return db.query(models.Order).all()
        orders = db.query(models.Order).filter(
            models.Order.user_email == email
        ).all()
        return orders

    @staticmethod
    @database_operation
    def remove_item(db: Session, email: str, product_id: str) -> None:
        """Remove an item from order (cart)"""
        active_order = db.query(models.Order).filter(
            models.Order.user_email == email,
            models.Order.status == OrderStatus.IN_PROGRESS
        ).first()
        if not active_order:
            raise BadRequest(details="No active cart")
        product = db.query(models.Product).filter(
            models.Product.id == product_id
        ).first()
        product.quantity += 1
        product.order_id = None
        db.delete(active_order)
        db.commit()

    @staticmethod
    @database_operation
    def submit(db: Session, order_id: str) -> models.Order:
        """Submit an order (finalize cart)"""
        order = db.query(models.Order).filter(
            models.Order.id == order_id
        ).first()

        if not order.products:
            raise NotFound(details="No items in cart")

        if order.status == OrderStatus.SUBMITTED:
            raise NotFound(details="Already Submitted")

        order.status = OrderStatus.SUBMITTED
        db.add(order)
        db.commit()
        return order

    @staticmethod
    @database_operation
    def cancel(db: Session, order_id: str, email:str) -> None:
        """Cancel (delete) order from db"""
        order = db.query(models.Order).filter(models.Order.id == order_id).first()
        if not order:
            raise NotFound(details="No such order exists!!")
        if order.user_email != email:
            raise Unauthorized(details="You are not authorized to cancel this order")
        
        products = (db.query(models.Product).join(models.Order,models.Product.order_id == models.Order.id).filter(models.Order.id == order_id).all())

        for product in products:
            product.quantity += 1
            product.order_id = None
        
        db.delete(order)
        db.commit()


    @staticmethod
    @database_operation
    def get_order_id_from_email(db: Session, email: str):
        order = db.query(models.Order).filter(models.Order.user_email == email,models.Order.status == OrderStatus.IN_PROGRESS).first()
        if not order:
            print("email:", repr(email), "status wanted:", repr(OrderStatus.IN_PROGRESS), flush=True)
            raise NotFound(details="No in-progress order found")
        return order.id


