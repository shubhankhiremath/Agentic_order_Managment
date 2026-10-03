from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config import get_settings


def make_engine(database_url: str | None = None):
    url = database_url or get_settings().database_url
    connect_args = {}
    if url.startswith("sqlite"):
        connect_args["check_same_thread"] = False
    return create_engine(url, connect_args=connect_args, future=True)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def configure_engine(database_url: str):
    global engine, SessionLocal
    engine = make_engine(database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return engine


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db(bind=None) -> None:
    from backend.database.base import Base
    from backend.database import models  # noqa: F401

    Base.metadata.create_all(bind or engine)
