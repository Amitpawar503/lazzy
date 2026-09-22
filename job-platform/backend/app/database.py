"""Database engine and session helpers (SQLModel over SQLite/Postgres)."""
from collections.abc import Iterator

from sqlmodel import Session, SQLModel, create_engine

from .config import get_settings

settings = get_settings()

# check_same_thread only matters for SQLite; SQLModel/SQLAlchemy ignores it otherwise.
connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, echo=False, connect_args=connect_args)


def init_db() -> None:
    # Import models so they register on SQLModel.metadata before create_all.
    from . import models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
