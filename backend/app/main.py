"""The StockRoom REST API."""

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import func, select, text
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import APP_NAME, APP_VERSION
from app.db import get_db
from app.models import Item
from app.schemas import ItemCreate, ItemOut, ItemUpdate, StatsOut

app = FastAPI(
    title=f"{APP_NAME} API",
    version=APP_VERSION,
    description="A stock control API for the DevOps capstone project.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=True)


# ---------------------------------------------------------------- service routes


@app.get("/", tags=["service"])
def root() -> dict:
    """Give the name and the version of the service."""
    return {"service": APP_NAME, "version": APP_VERSION, "docs": "/docs"}


@app.get("/health", tags=["service"])
def health() -> dict:
    """Report that the process is alive. Kubernetes uses this for the liveness probe."""
    return {"status": "healthy"}


@app.get("/ready", tags=["service"])
def ready(db: Session = Depends(get_db)) -> dict:
    """Make a test of the database connection. Kubernetes uses this for the readiness probe."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"database is not available: {error.__class__.__name__}",
        ) from error
    return {"status": "ready", "database": "connected"}


# ------------------------------------------------------------------- item routes
# The /stats route comes before the /{item_id} route.
# If the order is different, FastAPI reads the word "stats" as an identifier.


@app.get("/api/items/stats", response_model=StatsOut, tags=["items"])
def get_stats(db: Session = Depends(get_db)) -> StatsOut:
    """Give the totals of the store."""
    total_items = db.scalar(select(func.count(Item.id))) or 0
    total_units = db.scalar(select(func.coalesce(func.sum(Item.quantity), 0))) or 0
    total_value = db.scalar(
        select(func.coalesce(func.sum(Item.quantity * Item.unit_price), 0))
    ) or 0
    low_stock_items = db.scalar(
        select(func.count(Item.id)).where(Item.quantity <= Item.reorder_level)
    ) or 0
    categories = db.scalar(select(func.count(func.distinct(Item.category)))) or 0

    return StatsOut(
        total_items=int(total_items),
        total_units=int(total_units),
        total_value=round(float(total_value), 2),
        low_stock_items=int(low_stock_items),
        categories=int(categories),
    )


@app.get("/api/items", response_model=list[ItemOut], tags=["items"])
def list_items(
    category: str | None = None,
    low_stock: bool | None = None,
    db: Session = Depends(get_db),
) -> list[Item]:
    """Give all the items. The client can filter by category or by the low stock state."""
    query = select(Item).order_by(Item.id)
    if category:
        query = query.where(Item.category == category)
    if low_stock is True:
        query = query.where(Item.quantity <= Item.reorder_level)
    if low_stock is False:
        query = query.where(Item.quantity > Item.reorder_level)
    return list(db.scalars(query).all())


@app.get("/api/items/{item_id}", response_model=ItemOut, tags=["items"])
def get_item(item_id: int, db: Session = Depends(get_db)) -> Item:
    """Give one item."""
    return _find_item(item_id, db)


@app.post(
    "/api/items",
    response_model=ItemOut,
    status_code=status.HTTP_201_CREATED,
    tags=["items"],
)
def create_item(payload: ItemCreate, db: Session = Depends(get_db)) -> Item:
    """Make a new item."""
    item = Item(**payload.model_dump())
    db.add(item)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"the SKU {payload.sku} is already in use",
        ) from error
    db.refresh(item)
    return item


@app.put("/api/items/{item_id}", response_model=ItemOut, tags=["items"])
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)) -> Item:
    """Change one item. The client sends only the fields that change."""
    item = _find_item(item_id, db)
    changes = payload.model_dump(exclude_unset=True, exclude_none=True)
    if not changes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="the request body does not contain a field to change",
        )
    for field, value in changes.items():
        setattr(item, field, value)
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="the SKU is already in use",
        ) from error
    db.refresh(item)
    return item


@app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["items"])
def delete_item(item_id: int, db: Session = Depends(get_db)) -> None:
    """Delete one item."""
    item = _find_item(item_id, db)
    db.delete(item)
    db.commit()


def _find_item(item_id: int, db: Session) -> Item:
    """Give the item or stop the request with the code 404."""
    item = db.get(Item, item_id)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no item has the id {item_id}",
        )
    return item
