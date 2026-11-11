"""Request/response contracts (the public API of the Restaurant Service)."""
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class MenuItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = ""
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    is_veg: bool = True
    is_available: bool = True


class MenuItemUpdate(BaseModel):
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    is_available: bool | None = None
    description: str | None = None


class MenuItemOut(MenuItemCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    restaurant_id: int


class RestaurantCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    cuisine: str = Field(min_length=1, max_length=60)
    city: str = Field(min_length=1, max_length=60)
    address: str = Field(min_length=1, max_length=255)
    is_open: bool = True


class RestaurantStatusUpdate(BaseModel):
    is_open: bool


class RestaurantOut(RestaurantCreate):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime


class RestaurantDetail(RestaurantOut):
    menu_items: list[MenuItemOut] = []


# ---- Used by the Order Service (service-to-service collaboration) ----

class OrderLineRequest(BaseModel):
    menu_item_id: int
    quantity: int = Field(gt=0, le=50)


class ValidateOrderRequest(BaseModel):
    items: list[OrderLineRequest] = Field(min_length=1)


class PricedLine(BaseModel):
    menu_item_id: int
    name: str
    unit_price: Decimal
    quantity: int
    line_total: Decimal


class ValidateOrderResponse(BaseModel):
    restaurant_id: int
    restaurant_name: str
    lines: list[PricedLine]
    total_amount: Decimal
