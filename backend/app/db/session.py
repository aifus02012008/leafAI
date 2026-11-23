from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from app.core.config import settings


def _normalize_db_url(url: str) -> str:
    """Resolve the relative SQLite path and pick the psycopg 3 driver for Postgres URLs.

    Supabase/Render hand out ``postgres://`` or ``postgresql://`` URLs; SQLAlchemy needs
    an explicit driver to use psycopg 3.
    """
    if url.startswith("sqlite:///./"):
        return f"sqlite:///{settings.data_dir / 'leafai.db'}"
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


db_url = _normalize_db_url(settings.DATABASE_URL)
is_sqlite = db_url.startswith("sqlite")

engine = create_engine(
    db_url,
    connect_args={"check_same_thread": False} if is_sqlite else {},
    pool_pre_ping=not is_sqlite,
    echo=False,
)

if is_sqlite:
    @event.listens_for(engine, "connect")
    def _enable_sqlite_foreign_keys(dbapi_connection, _record):
        """SQLite ignores ON DELETE CASCADE / SET NULL unless foreign keys are switched on."""
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
