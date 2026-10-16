"""ORM models for the StockRoom application."""

from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Item(Base):
    """One stock item in the store."""

    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sku: Mapped[str] = mapped_column(String(40), nullable=False, unique=True, index=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False, default="general")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    reorder_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), default=_now
    )

    @property
    def stock_value(self) -> float:
        """Give the total value of this item."""
        return float(self.unit_price) * self.quantity

    @property
    def low_stock(self) -> bool:
        """Report True when the quantity is at or below the reorder level."""
        return self.quantity <= self.reorder_level
