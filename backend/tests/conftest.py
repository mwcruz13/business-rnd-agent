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
