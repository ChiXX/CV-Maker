import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator, List, Annotated
from sqlalchemy import inspect, text
from sqlalchemy.pool import StaticPool
from fastapi import Depends
from models import Base

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

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)

def ensure_columns_exist():
    """Ensure optional columns exist on the applications table (adds them if missing)."""
    inspector = inspect(engine)
    if "applications" not in inspector.get_table_names():
        return

    existing_columns: List[str] = [c["name"] for c in inspector.get_columns("applications")]

    with engine.begin() as conn:
        if "cv_latex" not in existing_columns:
            conn.execute(text('ALTER TABLE applications ADD COLUMN cv_latex TEXT'))
        if "cl_latex" not in existing_columns:
            conn.execute(text('ALTER TABLE applications ADD COLUMN cl_latex TEXT'))

def init_db():
    """Initialize database and create tables"""
    create_tables()
    # Ensure schema is up-to-date for fields added after initial table creation.
    try:
        ensure_columns_exist()
    except Exception:
        # If ALTER fails in some environments, ignore so app can still start.
        pass
