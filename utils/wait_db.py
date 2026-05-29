"""Wait until the database is ready to accept connections (Docker startup)."""

import time

from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from db import db


def wait_for_db(max_retries: int = 30, delay: float = 2.0) -> None:
    """Retry database connection before running migrations/seeds."""
    for attempt in range(1, max_retries + 1):
        try:
            db.session.execute(text("SELECT 1"))
            db.session.commit()
            return
        except OperationalError:
            db.session.rollback()
            if attempt == max_retries:
                raise
            time.sleep(delay)
