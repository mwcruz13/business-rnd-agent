import os
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# ---------------------------------------------------------------------------
# Redirect ALL tests to the dedicated bmi_test database so test data never
# pollutes the production "postgres" database.
#
# This MUST happen before any production module is imported, because
# backend.app.config.get_settings() is cached and backend.app.db.session
# creates the engine at import time.
# ---------------------------------------------------------------------------
os.environ["POSTGRES_DB"] = "bmi_test"

# Clear the cached Settings singleton so it picks up the new env var.
from backend.app.config import get_settings          # noqa: E402
get_settings.cache_clear()

# Now force-reinitialise the engine and SessionLocal with the test DB URL.
import backend.app.db.session as _sess_mod           # noqa: E402
from sqlalchemy import create_engine                  # noqa: E402
from sqlalchemy.orm import sessionmaker               # noqa: E402

_test_engine = create_engine(get_settings().database_url, future=True)
_test_session_local = sessionmaker(
    bind=_test_engine, autoflush=False, autocommit=False, future=True,
)
_sess_mod.engine = _test_engine
_sess_mod.SessionLocal = _test_session_local
_sess_mod._schema_validated = False                   # force re-check on test DB

# Create all tables in the test database (idempotent).
from backend.app.db.models import Base                # noqa: E402
Base.metadata.create_all(_test_engine)

# Ensure columns added after initial table creation are present.
from sqlalchemy import inspect as _sa_inspect, text as _sa_text  # noqa: E402
_insp = _sa_inspect(_test_engine)
for _table in Base.metadata.sorted_tables:
    if _table.name not in _insp.get_table_names():
        continue
    _existing_cols = {c["name"] for c in _insp.get_columns(_table.name)}
    for _col in _table.columns:
        if _col.name not in _existing_cols:
            _col_type = _col.type.compile(dialect=_test_engine.dialect)
            with _test_engine.connect() as _conn:
                _conn.execute(_sa_text(
                    f'ALTER TABLE {_table.name} ADD COLUMN {_col.name} {_col_type}'
                ))
                _conn.commit()
