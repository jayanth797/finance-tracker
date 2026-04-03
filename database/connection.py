"""
Database connection configuration using SQLAlchemy.
Uses SQLite for portability; swap DATABASE_URL for PostgreSQL/MySQL in production.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = "sqlite:///./finance_tracker.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # required for SQLite
    echo=False,  # set True to log SQL queries during development
)


class Base(DeclarativeBase):
    """Shared declarative base for all SQLAlchemy models."""
    pass
