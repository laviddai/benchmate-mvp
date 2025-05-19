# backend/app/db/session.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session as SQLAlchemySession # Renaming for clarity
from typing import Generator

from app.core.config import settings # Import the settings instance

# Create the SQLAlchemy engine
# The engine is the starting point for any SQLAlchemy application.
# It's the 'home base' for the actual database, providing a connectivity pool.
# connect_args is for specific driver arguments. For SQLite, it's {'check_same_thread': False}.
# For PostgreSQL with psycopg2, it's often not needed unless you have very specific requirements.
# pool_pre_ping=True: enables SQLAlchemy to test connections for liveness before handing them out
# from the pool, which can help with connections that have timed out.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True
    # echo=True # Set to True to see generated SQL in logs, useful for debugging
)

# Create a configured "Session" class
# This SessionLocal class will be used to create individual database sessions.
# autocommit=False: Transactions are not committed automatically. You must call session.commit().
# autoflush=False: Changes are not automatically flushed to the DB before queries.
#                You might need to call session.flush() manually in some cases or rely on commit.
# bind=engine: Associates this Session factory with our database engine.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# Dependency for FastAPI endpoints to get a DB session
def get_db() -> Generator[SQLAlchemySession, None, None]:
    """
    FastAPI dependency that provides a SQLAlchemy database session.

    It ensures that the database session is always closed after the request,
    even if there was an exception.
    """
    db = SessionLocal()
    try:
        yield db  # Provide the session to the endpoint
    finally:
        db.close() # Close the session when the request is done