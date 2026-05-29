"""Lightweight schema migrations for existing databases."""

from sqlalchemy import inspect, text

from db import db


def _column_names(table: str) -> set[str]:
    inspector = inspect(db.engine)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def run_migrations() -> None:
    """Apply additive schema changes that create_all() does not handle."""
    user_cols = _column_names("users")
    if user_cols and "role" not in user_cols:
        db.session.execute(
            text(
                "ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'customer'"
            )
        )
        db.session.commit()

    store_cols = _column_names("stores")
    if store_cols and "owner_id" not in store_cols:
        dialect = db.engine.dialect.name
        if dialect == "postgresql":
            db.session.execute(
                text(
                    "ALTER TABLE stores ADD COLUMN owner_id INTEGER "
                    "REFERENCES users(id) ON DELETE CASCADE"
                )
            )
        elif dialect == "mysql":
            db.session.execute(text("ALTER TABLE stores ADD COLUMN owner_id INTEGER NULL"))
            db.session.execute(
                text(
                    "ALTER TABLE stores ADD CONSTRAINT fk_stores_owner "
                    "FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE CASCADE"
                )
            )
        else:
            db.session.execute(text("ALTER TABLE stores ADD COLUMN owner_id INTEGER"))
        db.session.commit()
