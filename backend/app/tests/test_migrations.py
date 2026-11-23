"""Migration tests: fresh databases and legacy (pre-Alembic) databases."""
from sqlalchemy import create_engine, inspect, text

from app.db.migrate import run_migrations

LEGACY_SCHEMA = [
    """CREATE TABLE users (id INTEGER NOT NULL, email VARCHAR(255) NOT NULL,
       password_hash VARCHAR(255) NOT NULL, created_at DATETIME NOT NULL,
       updated_at DATETIME NOT NULL, PRIMARY KEY (id))""",
    "CREATE UNIQUE INDEX ix_users_email ON users (email)",
    "CREATE INDEX ix_users_id ON users (id)",
    """CREATE TABLE diseases (id INTEGER NOT NULL, class_name VARCHAR(100) NOT NULL,
       display_name VARCHAR(200) NOT NULL, description TEXT, symptoms TEXT,
       prevention TEXT, treatment TEXT, image_path VARCHAR(500),
       created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, PRIMARY KEY (id))""",
    "CREATE INDEX ix_diseases_id ON diseases (id)",
    "CREATE UNIQUE INDEX ix_diseases_class_name ON diseases (class_name)",
    """CREATE TABLE diagnosis_history (id INTEGER NOT NULL, user_id INTEGER NOT NULL,
       original_image_path VARCHAR(500) NOT NULL, result_image_path VARCHAR(500),
       status VARCHAR(50) NOT NULL, inference_time FLOAT, created_at DATETIME NOT NULL,
       PRIMARY KEY (id), FOREIGN KEY(user_id) REFERENCES users (id) ON DELETE CASCADE)""",
    "CREATE INDEX ix_diagnosis_history_id ON diagnosis_history (id)",
    "CREATE INDEX ix_diagnosis_history_user_id ON diagnosis_history (user_id)",
    """CREATE TABLE detection_results (id INTEGER NOT NULL, history_id INTEGER NOT NULL,
       class_name VARCHAR(100) NOT NULL, confidence FLOAT NOT NULL, x1 FLOAT NOT NULL,
       y1 FLOAT NOT NULL, x2 FLOAT NOT NULL, y2 FLOAT NOT NULL, created_at DATETIME NOT NULL,
       PRIMARY KEY (id), FOREIGN KEY(history_id) REFERENCES diagnosis_history (id) ON DELETE CASCADE)""",
    "CREATE INDEX ix_detection_results_history_id ON detection_results (history_id)",
    "CREATE INDEX ix_detection_results_id ON detection_results (id)",
]


def _engine(tmp_path, name):
    return create_engine(f"sqlite:///{tmp_path / name}")


def _columns(engine, table):
    return {col["name"] for col in inspect(engine).get_columns(table)}


def test_fresh_database_gets_full_schema(tmp_path):
    engine = _engine(tmp_path, "fresh.db")
    run_migrations(engine)

    tables = set(inspect(engine).get_table_names())
    assert {"users", "diseases", "diagnosis_history", "detection_results", "alembic_version"} <= tables
    assert {"crop_code", "model_version", "user_feedback", "feedback_at"} <= _columns(engine, "diagnosis_history")
    assert {"crop_code", "treatment_steps", "recovery_info"} <= _columns(engine, "diseases")


def test_migrations_are_idempotent(tmp_path):
    engine = _engine(tmp_path, "twice.db")
    run_migrations(engine)
    run_migrations(engine)
    assert "crop_code" in _columns(engine, "diseases")


def test_legacy_database_is_upgraded_without_data_loss(tmp_path):
    engine = _engine(tmp_path, "legacy.db")
    with engine.begin() as conn:
        for stmt in LEGACY_SCHEMA:
            conn.execute(text(stmt))
        conn.execute(text(
            "INSERT INTO users VALUES (1, 'a@b.dev', 'x', '2026-01-01', '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO diagnosis_history VALUES (1, 1, 'originals/a.jpg', NULL, 'detected', 0.1, '2026-01-01')"
        ))
        conn.execute(text(
            "INSERT INTO diseases (id, class_name, display_name, created_at, updated_at) "
            "VALUES (1, 'Brown Blight', 'Brown Blight', '2026-01-01', '2026-01-01')"
        ))

    run_migrations(engine)

    with engine.connect() as conn:
        crop = conn.execute(text("SELECT crop_code FROM diagnosis_history WHERE id = 1")).scalar()
        disease_crop = conn.execute(text("SELECT crop_code FROM diseases WHERE id = 1")).scalar()
    assert crop == "tea"
    assert disease_crop == "tea"
    assert {"treatment_steps", "recovery_info"} <= _columns(engine, "diseases")


def test_same_disease_name_allowed_for_different_crops(tmp_path):
    engine = _engine(tmp_path, "unique.db")
    run_migrations(engine)
    insert = text(
        "INSERT INTO diseases (class_name, display_name, crop_code, created_at, updated_at) "
        "VALUES ('Anthracnose', 'Anthracnose', :crop, '2026-01-01', '2026-01-01')"
    )
    with engine.begin() as conn:
        conn.execute(insert, {"crop": "durian"})
        conn.execute(insert, {"crop": "rambutan"})
        count = conn.execute(text("SELECT COUNT(*) FROM diseases")).scalar()
    assert count == 2


def test_downgrade_does_not_cascade_delete_children(tmp_path):
    """Batch table recreation must not fire ON DELETE CASCADE (FKs are on in the app engine)."""
    from alembic import command
    from app.db.migrate import _alembic_config
    from sqlalchemy import event

    engine = _engine(tmp_path, "fk.db")

    @event.listens_for(engine, "connect")
    def _fk_on(dbapi_conn, _rec):
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    run_migrations(engine)
    with engine.begin() as conn:
        conn.execute(text("INSERT INTO users VALUES (1, 'a@b.dev', 'x', '2026-01-01', '2026-01-01')"))
        conn.execute(text(
            "INSERT INTO diagnosis_history (id, user_id, original_image_path, status, created_at, crop_code) "
            "VALUES (1, 1, 'o.jpg', 'detected', '2026-01-01', 'tea')"
        ))
        conn.execute(text(
            "INSERT INTO detection_results VALUES (1, 1, 'X', 0.9, 0, 0, 1, 1, '2026-01-01')"
        ))

    cfg = _alembic_config()
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys=OFF")
        conn.commit()
        with conn.begin():
            cfg.attributes["connection"] = conn
            command.downgrade(cfg, "0002_multi_crop")
    with engine.connect() as conn:
        assert conn.execute(text("SELECT COUNT(*) FROM detection_results")).scalar() == 1
