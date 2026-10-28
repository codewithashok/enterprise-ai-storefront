from fastapi import APIRouter, HTTPException, status

from app.core.security import CurrentUser
from app.db.models import Order
from app.db.session import DbSession
from app.schemas.order import CartItemAdd, CartItemUpdate, OrderRead
from app.services import order_service
from app.services.order_service import (
    CartItemNotFoundError,
    InsufficientStockError,
    ProductUnavailableError,
)

cart_router = APIRouter(prefix="/cart", tags=["cart"])
orders_router = APIRouter(prefix="/orders", tags=["orders"])


@cart_router.get("", response_model=OrderRead)
async def get_cart(user: CurrentUser, db: DbSession) -> Order:
    return await order_service.get_or_create_cart(db, user.id)


@cart_router.post("/items", response_model=OrderRead)
async def add_cart_item(body: CartItemAdd, user: CurrentUser, db: DbSession) -> Order:
    try:
        return await order_service.add_item(db, user.id, body.product_id, body.quantity)
    except ProductUnavailableError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None


@cart_router.patch("/items/{item_id}", response_model=OrderRead)
async def update_cart_item(item_id: int, body: CartItemUpdate, user: CurrentUser, db: DbSession) -> Order:
    try:
        return await order_service.update_item(db, user.id, item_id, body.quantity)
    except CartItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None
    except InsufficientStockError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from None


@cart_router.delete("/items/{item_id}", response_model=OrderRead)
async def remove_cart_item(item_id: int, user: CurrentUser, db: DbSession) -> Order:
    try:
        return await order_service.update_item(db, user.id, item_id, 0)
    except CartItemNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, str(exc)) from None


@orders_router.get("", response_model=list[OrderRead])
async def list_orders(user: CurrentUser, db: DbSession) -> list[Order]:
    return await order_service.list_orders(db, user.id)


@orders_router.get("/{order_id}", response_model=OrderRead)
async def get_order(order_id: int, user: CurrentUser, db: DbSession) -> Order:
    order = await order_service.get_order(db, user.id, order_id)
    if order is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Order not found")
    return order
