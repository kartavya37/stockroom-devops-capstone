"""Database engine, session factory and the declarative base."""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Parent class of every ORM model."""


def get_db() -> Generator[Session, None, None]:
    """Give one database session to a request and close it afterwards."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
