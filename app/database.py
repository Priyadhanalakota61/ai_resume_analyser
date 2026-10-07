import os

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import AnalysisRecord, Base


class DatabaseConfigurationError(RuntimeError):
    """Raised when the database connection string is missing."""


class DatabaseSaveError(RuntimeError):
    """Raised when an analysis cannot be saved."""


def save_analysis(resume_text: str, generated_result: dict) -> int:
    database_url = os.getenv("DATABASE_URL", "").strip()
    if not database_url:
        raise DatabaseConfigurationError(
            "DATABASE_URL is not configured. Add your MySQL connection string to .env."
        )

    engine = create_engine(database_url, pool_pre_ping=True)
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
        raise DatabaseSaveError(
            "The analysis could not be saved. Check that MySQL is running and the database exists."
        ) from exc
    finally:
        engine.dispose()
