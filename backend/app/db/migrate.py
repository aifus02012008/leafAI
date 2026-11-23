"""Programmatic Alembic runner used at application startup and in tests."""
from __future__ import annotations

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text
from sqlalchemy.engine import Connection, Engine

logger = logging.getLogger(__name__)

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"
BASELINE_REVISION = "0001_baseline"
# Columns that older builds added with ad-hoc ALTER TABLE before Alembic existed.
LEGACY_DISEASE_COLUMNS = ("treatment_steps", "recovery_info")


def _alembic_config() -> Config:
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS_DIR))
    return cfg


def _is_unversioned_legacy_db(conn: Connection) -> bool:
    insp = inspect(conn)
    return insp.has_table("users") and not insp.has_table("alembic_version")


def _patch_legacy_columns(conn: Connection) -> None:
    existing = {col["name"] for col in inspect(conn).get_columns("diseases")}
    for column in LEGACY_DISEASE_COLUMNS:
        if column not in existing:
            conn.execute(text(f"ALTER TABLE diseases ADD COLUMN {column} TEXT"))
            logger.info("Added legacy column diseases.%s before baselining.", column)


def run_migrations(target_engine: Engine | None = None) -> None:
    """Bring the database schema to the latest revision.

    Databases created before Alembic was introduced are first stamped with the
    baseline revision so their existing tables and data are kept.
    """
    if target_engine is None:
        from app.db.session import engine as target_engine

    cfg = _alembic_config()
    is_sqlite = target_engine.dialect.name == "sqlite"
    with target_engine.connect() as conn:
        if is_sqlite:
            # Batch migrations recreate tables (DROP + rename); with foreign keys on, that
            # would fire ON DELETE CASCADE / SET NULL on child tables. Must run outside a transaction.
            conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
            conn.commit()  # close SQLAlchemy's autobegun transaction before begin()
        try:
            with conn.begin():
                cfg.attributes["connection"] = conn
                if _is_unversioned_legacy_db(conn):
                    _patch_legacy_columns(conn)
                    command.stamp(cfg, BASELINE_REVISION)
                    logger.info("Stamped existing database at %s.", BASELINE_REVISION)
                command.upgrade(cfg, "head")
        finally:
            if is_sqlite:
                conn.exec_driver_sql("PRAGMA foreign_keys=ON")
                conn.commit()
