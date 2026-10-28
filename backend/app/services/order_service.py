"""Cart and order logic shared by the REST API and (later) the agent tools.

Every function takes the acting user_id from the verified JWT. It is never
accepted from request bodies or LLM output.
"""

import uuid

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer, selectinload

from app.db.models import Order, OrderItem, OrderStatus, Product
from app.schemas.order import compute_total
from app.services import catalog_service


class ProductUnavailableError(Exception):
    pass


class InsufficientStockError(Exception):
    pass


class CartItemNotFoundError(Exception):
    pass


# Async SQLAlchemy can't lazy-load, so relationships are fetched up front
_ORDER_LOAD = selectinload(Order.items).selectinload(OrderItem.product).options(defer(Product.embedding))


async def _load_cart(db: AsyncSession, user_id: uuid.UUID) -> Order:
    cart = await db.scalar(
        select(Order)
        .options(_ORDER_LOAD)
        .where(Order.user_id == user_id, Order.status == OrderStatus.CART)
        .execution_options(populate_existing=True)
    )
    assert cart is not None
    return cart


async def get_or_create_cart(db: AsyncSession, user_id: uuid.UUID) -> Order:
    # Race-safe: two concurrent requests can't create two carts (partial unique index)
    await db.execute(
        insert(Order)
        .values(user_id=user_id, status=OrderStatus.CART)
        .on_conflict_do_nothing(index_elements=[Order.user_id], index_where=text("status = 'cart'"))
    )
    await db.commit()
    return await _load_cart(db, user_id)


async def add_item(db: AsyncSession, user_id: uuid.UUID, product_id: int, quantity: int) -> Order:
    product = await catalog_service.get_product(db, product_id, item_state="available")
    if product is None:
        raise ProductUnavailableError("Product is not available")

    cart = await get_or_create_cart(db, user_id)
    line = next((item for item in cart.items if item.product_id == product_id), None)
    new_quantity = (line.quantity if line else 0) + quantity
    if new_quantity > product.inventory_count:
        raise InsufficientStockError(f"Only {product.inventory_count} left in stock")

    if line:
        line.quantity = new_quantity
    else:
        cart.items.append(OrderItem(product_id=product.id, quantity=quantity, unit_price=product.price))

    cart.total_amount = compute_total(cart.items)
    await db.commit()
    return await _load_cart(db, user_id)


async def update_item(db: AsyncSession, user_id: uuid.UUID, item_id: int, quantity: int) -> Order:
    cart = await get_or_create_cart(db, user_id)
    line = next((item for item in cart.items if item.id == item_id), None)
    if line is None:
        raise CartItemNotFoundError("Item is not in your cart")

    if quantity == 0:
        cart.items.remove(line)  # delete-orphan cascade deletes the row
    elif quantity > line.product.inventory_count:
        raise InsufficientStockError(f"Only {line.product.inventory_count} left in stock")
    else:
        line.quantity = quantity

    cart.total_amount = compute_total(cart.items)
    await db.commit()
    return await _load_cart(db, user_id)


async def list_orders(db: AsyncSession, user_id: uuid.UUID) -> list[Order]:
    rows = await db.scalars(
        select(Order)
        .options(_ORDER_LOAD)
        .where(Order.user_id == user_id, Order.status != OrderStatus.CART)
        .order_by(Order.created_at.desc())
    )
    return list(rows)


async def get_order(db: AsyncSession, user_id: uuid.UUID, order_id: int) -> Order | None:
    # Filtering by user_id means another user's order is indistinguishable from "not found"
    return await db.scalar(
        select(Order).options(_ORDER_LOAD).where(Order.id == order_id, Order.user_id == user_id)
    )
