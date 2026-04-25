from sqlalchemy import create_engine
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker

from backend.app.config import get_settings


settings = get_settings()
engine = create_engine(settings.database_url, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
REQUIRED_RUNTIME_TABLES = frozenset({"runs", "step_outputs", "checkpoints", "signal_reports", "signal_records"})
_schema_validated = False


class DatabaseSchemaNotReadyError(RuntimeError):
	pass


def ensure_database_schema() -> None:
	global _schema_validated

	if _schema_validated:
		return

	inspector = inspect(engine)
	existing_tables = set(inspector.get_table_names())
	missing_tables = sorted(REQUIRED_RUNTIME_TABLES - existing_tables)
	if missing_tables:
		missing = ", ".join(missing_tables)
		raise DatabaseSchemaNotReadyError(
			f"Database schema is not initialized. Missing tables: {missing}. Run `make migrate` inside the project root."
		)

	_schema_validated = True
