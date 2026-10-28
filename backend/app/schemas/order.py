from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.db.models import OrderStatus
from app.schemas.catalog import Money

MAX_QTY_PER_LINE = 20


class CartItemAdd(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=MAX_QTY_PER_LINE)


class CartItemUpdate(BaseModel):
    quantity: int = Field(ge=0, le=MAX_QTY_PER_LINE)  # 0 removes the line


class ProductSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    category: str


class OrderItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    quantity: int
    unit_price: Money
    product: ProductSummary

    @computed_field
    @property
    def line_total(self) -> Money:
        return self.unit_price * self.quantity


class OrderRead(BaseModel):
    """Used for both the cart (status='cart') and placed orders."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    status: OrderStatus
    total_amount: Money
    created_at: datetime
    items: list[OrderItemRead]

    @computed_field
    @property
    def item_count(self) -> int:
        return sum(item.quantity for item in self.items)


def compute_total(items: list) -> Decimal:
    return sum((item.unit_price * item.quantity for item in items), Decimal("0.00"))
