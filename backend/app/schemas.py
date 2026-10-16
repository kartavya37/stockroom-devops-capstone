"""Pydantic schemas that validate the request and response bodies."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ItemBase(BaseModel):
    """Fields that a client can send for an item."""

    name: str = Field(min_length=1, max_length=120)
    sku: str = Field(min_length=1, max_length=40)
    category: str = Field(default="general", max_length=60)
    quantity: int = Field(default=0, ge=0)
    unit_price: float = Field(default=0, ge=0)
    reorder_level: int = Field(default=0, ge=0)


class ItemCreate(ItemBase):
    """Body of a POST request."""


class ItemUpdate(BaseModel):
    """Body of a PUT request. Every field is optional."""

    name: str | None = Field(default=None, min_length=1, max_length=120)
    sku: str | None = Field(default=None, min_length=1, max_length=40)
    category: str | None = Field(default=None, max_length=60)
    quantity: int | None = Field(default=None, ge=0)
    unit_price: float | None = Field(default=None, ge=0)
    reorder_level: int | None = Field(default=None, ge=0)


class ItemOut(ItemBase):
    """Body of a response that contains one item."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    stock_value: float
    low_stock: bool


class StatsOut(BaseModel):
    """Body of the statistics response."""

    total_items: int
    total_units: int
    total_value: float
    low_stock_items: int
    categories: int
