"""
Database session management.
Provides a FastAPI dependency that yields a scoped DB session per request.
"""

from typing import Generator
from sqlalchemy.orm import Session, sessionmaker

from database.connection import engine

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency that provides a database session.
    Automatically closes the session after the request is complete.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
