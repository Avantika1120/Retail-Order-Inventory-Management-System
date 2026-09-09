from decimal import Decimal
from typing import List

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    sku: str
    name: str
    category: str
    price: Decimal = Field(gt=0)
    opening_stock: int = Field(default=0, ge=0)
    reorder_level: int = Field(default=5, ge=0)


class ProductRead(ORMModel):
    id: int
    sku: str
    name: str
    category: str
    price: Decimal


class CustomerCreate(BaseModel):
    name: str
    email: EmailStr


class CustomerRead(ORMModel):
    id: int
    name: str
    email: EmailStr


class InventoryRead(BaseModel):
    product_id: int
    quantity_on_hand: int
    reorder_level: int


class RestockRequest(BaseModel):
    quantity: int = Field(gt=0)


class OrderLineCreate(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderLineCreate]


class OrderRead(BaseModel):
    id: int
    customer_id: int
    status: str
    total_amount: Decimal


class ReviewCreate(BaseModel):
    product_id: int
    customer_id: int | None = None
    rating: int = Field(ge=1, le=5)
    title: str
    body: str


class ReviewRead(ReviewCreate):
    id: str


class ReviewSummary(BaseModel):
    product_id: int
    review_count: int
    summary: str
