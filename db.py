"""
Database module: central SQLAlchemy instance.

Separates db from models and the app factory to avoid circular imports,
following Application Factory and clean architecture layering.
"""

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """SQLAlchemy 2.x declarative base class."""


db = SQLAlchemy(model_class=Base)
