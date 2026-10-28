"""Catalog queries shared by the REST API and (later) the agent tools.

All visibility rules live here, so the API and the LLM can never disagree about
what a shopper is allowed to see.
"""

from sqlalchemy import ColumnElement, and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import defer

from app.db.models import Product
from app.schemas.catalog import ItemState, ProductQuery


def visibility_clause(item_state: ItemState) -> ColumnElement[bool]:
    """Translate the business alias into the real SQL predicate."""
    clause = and_(Product.is_active.is_(True), Product.is_deleted.is_(False))
    if item_state == "available":
        clause = and_(clause, Product.inventory_count > 0)
    return clause


async def list_products(db: AsyncSession, query: ProductQuery) -> tuple[list[Product], int]:
    filters = [visibility_clause(query.item_state)]
    if query.category:
        filters.append(Product.category == query.category)
    if query.min_price is not None:
        filters.append(Product.price >= query.min_price)
    if query.max_price is not None:
        filters.append(Product.price <= query.max_price)

    total = await db.scalar(select(func.count()).select_from(Product).where(*filters))
    rows = await db.scalars(
        select(Product)
        .options(defer(Product.embedding))  # 1536 floats per row we don't need here
        .where(*filters)
        .order_by(Product.category, Product.name)
        .limit(query.limit)
        .offset(query.offset)
    )
    return list(rows), total or 0


async def get_product(db: AsyncSession, product_id: int, item_state: ItemState = "all") -> Product | None:
    return await db.scalar(
        select(Product)
        .options(defer(Product.embedding))
        .where(Product.id == product_id, visibility_clause(item_state))
    )


async def list_categories(db: AsyncSession) -> list[str]:
    rows = await db.scalars(
        select(Product.category).where(visibility_clause("all")).distinct().order_by(Product.category)
    )
    return list(rows)
