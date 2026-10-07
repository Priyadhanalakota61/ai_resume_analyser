import os

from sqlalchemy import create_engine
from sqlalchemy.exc import ArgumentError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import AnalysisRecord, Base


class DatabaseConfigurationError(RuntimeError):
    """Raised when the database connection string is missing or invalid."""


class DatabaseSaveError(RuntimeError):
    """Raised when an analysis cannot be saved."""


def _create_engine():
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL is not configured. Add your MySQL connection string to .env."
        )
    if not database_url.startswith("mysql"):
        raise DatabaseConfigurationError("DATABASE_URL must point to a MySQL database.")

    try:
        return create_engine(database_url, pool_pre_ping=True)
    except ArgumentError as exc:
        raise DatabaseConfigurationError("DATABASE_URL is not a valid SQLAlchemy MySQL URL.") from exc


def ensure_database_ready() -> None:
    engine = _create_engine()
    try:
        Base.metadata.create_all(engine)
    except SQLAlchemyError as exc:
        raise DatabaseSaveError(
            "MySQL is not ready. Check that the server is running and the configured database exists."
        ) from exc
    finally:
        engine.dispose()


def save_analysis(resume_text: str, generated_result: dict) -> int:
    engine = _create_engine()
    try:
        Base.metadata.create_all(engine)
        with Session(engine) as session:
            record = AnalysisRecord(
                resume_text=resume_text,
                generated_result=generated_result,
            )
            session.add(record)
            session.commit()
            return record.id
    except SQLAlchemyError as exc:
        raise DatabaseSaveError("The analysis could not be saved to MySQL.") from exc
    finally:
        engine.dispose()
