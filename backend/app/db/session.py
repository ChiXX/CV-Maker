import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, List, Annotated
from sqlalchemy import inspect, text
from sqlalchemy.pool import StaticPool
from fastapi import Depends
from app.db.models import Base

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://cv_user:cv_password@localhost:5432/cv_maker")

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=StaticPool,
    connect_args={
        "check_same_thread": False,
    } if DATABASE_URL.startswith("sqlite") else {},
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Dependency to get database session as a generator.

    Use as:
        db = next(get_db())
    or as a FastAPI dependency.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# FastAPI dependency for database session
def get_db_dependency(db: Session = Depends(get_db)) -> Session:
    """FastAPI dependency for database session"""
    return db

def init_db():
    """
    Initialize database.
    Note: Schema management is now handled by Alembic migrations.
    """
    # For backward compatibility, this function is kept but has no effect on schema.
    # The actual table creation should be done via: alembic upgrade head
    pass
