"""Database bootstrap: apply migrations, then sync the disease library."""
import logging

from app.db.migrate import run_migrations
from app.db.seed import seed_diseases
from app.db.session import SessionLocal

logger = logging.getLogger(__name__)


def init_database() -> None:
    """Bring the schema to the latest Alembic revision and seed all crop disease catalogs."""
    run_migrations()
    db = SessionLocal()
    try:
        seed_diseases(db)
    finally:
        db.close()
