# backend/app/db/base_class.py
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import MetaData

# Optional: Define naming conventions for database indexes and constraints.
# This helps in having consistent names for these objects in your database schema,
# which is particularly useful for Alembic migrations and when inspecting the DB.
# See SQLAlchemy documentation for more details on these conventions.
convention = {
    "ix": "ix_%(column_0_label)s",                          # Index
    "uq": "uq_%(table_name)s_%(column_0_name)s",            # Unique constraint
    "ck": "ck_%(table_name)s_%(constraint_name)s",          # Check constraint
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s", # Foreign key
    "pk": "pk_%(table_name)s",                              # Primary key
}

# Create a base class for all our ORM models to inherit from.
# This Base class will hold the metadata for all tables.
class Base(DeclarativeBase):
    """
    Base class for SQLAlchemy ORM models.
    It includes a MetaData instance with a naming convention.
    """
    metadata = MetaData(naming_convention=convention)