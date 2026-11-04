from pathlib import Path
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
def test_alembic_applies_schema_and_competition_date(tmp_path):
    database = tmp_path / "migration_test.db"
    project = Path(__file__).resolve().parents[2]
    cfg = Config(str(project / "alembic.ini")); cfg.set_main_option("script_location", str(project / "migrations")); cfg.set_main_option("sqlalchemy.url", f"sqlite:///{database.as_posix()}")
    command.upgrade(cfg, "head")
    engine = create_engine(f"sqlite:///{database.as_posix()}")
    inspector = inspect(engine)
    assert {"sports", "athletes", "results"}.issubset(set(inspector.get_table_names()))
    assert "competition_date" in {column["name"] for column in inspector.get_columns("results")}
    engine.dispose()
