from typing import Annotated

from fastapi import APIRouter, HTTPException, Query, status

from app.db.models import Product
from app.db.session import DbSession
from app.schemas.catalog import ProductPage, ProductQuery, ProductRead
from app.services import catalog_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ProductPage)
async def list_products(query: Annotated[ProductQuery, Query()], db: DbSession) -> ProductPage:
    products, total = await catalog_service.list_products(db, query)
    return ProductPage(
        items=[ProductRead.model_validate(p) for p in products],
        total=total,
        limit=query.limit,
        offset=query.offset,
    )


@router.get("/categories", response_model=list[str])
async def list_categories(db: DbSession) -> list[str]:
    return await catalog_service.list_categories(db)


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, db: DbSession) -> Product:
    product = await catalog_service.get_product(db, product_id)
    if product is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Product not found")
    return product
