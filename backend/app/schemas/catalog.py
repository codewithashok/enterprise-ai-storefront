from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PlainSerializer, computed_field, model_validator

# Decimal in Python (exact math), plain number in JSON (easy for the frontend)
Money = Annotated[Decimal, PlainSerializer(float, return_type=float, when_used="json")]

# Business-level alias the API and LLM tools use instead of raw DB flags:
#   available -> active, not deleted, inventory > 0
#   all       -> active, not deleted (includes out-of-stock)
ItemState = Literal["available", "all"]


class ProductRead(BaseModel):
    """Public product shape. cost_price, is_active, is_deleted, embedding never leave the API."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    description: str
    category: str
    price: Money
    inventory_count: int = Field(exclude=True)  # read from the row, but not serialized

    @computed_field
    @property
    def in_stock(self) -> bool:
        return self.inventory_count > 0


class ProductQuery(BaseModel):
    """Query params for GET /products."""

    category: str | None = None
    min_price: Decimal | None = Field(default=None, ge=0)
    max_price: Decimal | None = Field(default=None, ge=0)
    item_state: ItemState = "available"
    limit: int = Field(default=20, ge=1, le=100)
    offset: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def check_price_range(self) -> "ProductQuery":
        if self.min_price is not None and self.max_price is not None and self.min_price > self.max_price:
            raise ValueError("min_price cannot be greater than max_price")
        return self


class ProductPage(BaseModel):
    items: list[ProductRead]
    total: int
    limit: int
    offset: int
