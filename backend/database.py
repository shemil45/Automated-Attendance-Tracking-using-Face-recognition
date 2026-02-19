"""
Database configuration and setup
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

import os

# Load .env file so DATABASE_URL and other vars are available
load_dotenv()

# Database URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./attendance.db")

# Fix for Render's postgres:// URLs (SQLAlchemy requires postgresql://)
if SQLALCHEMY_DATABASE_URL and SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

is_sqlite = "sqlite" in SQLALCHEMY_DATABASE_URL

# Connect args (only for SQLite)
connect_args = {"check_same_thread": False} if is_sqlite else {}

# Create engine
# For Supabase (PostgreSQL via PgBouncer pooler in transaction mode) we use NullPool
# so SQLAlchemy does not hold open idle connections. Each request borrows a connection
# from PgBouncer and returns it immediately — multiple local backends can share the
# same Supabase project without hitting the connection limit.
if is_sqlite:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
    )
else:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        poolclass=NullPool,       # Don't keep idle connections open
        pool_pre_ping=True,       # Verify connection is alive before use
    )

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database
def init_db():
    """Create all tables"""
    from . import models  # Import models to register them
    Base.metadata.create_all(bind=engine)
