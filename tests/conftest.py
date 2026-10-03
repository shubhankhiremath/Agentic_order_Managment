from pathlib import Path

import pytest
from sqlalchemy.orm import Session

from backend.config import PROJECT_ROOT, get_settings
from backend.database.import_data import import_dataset
from backend.database.session import SessionLocal, configure_engine, init_db

SAMPLE_ORDER_IDS = [
    "e481f51cbdc54678b7cc49136f2d6af7",  # on-time delivered
    "203096f03d82e0dffbc41ebc2e2bcfb7",  # late delivered
    "ee64d42b8cf066f35eac1cf57de1aa85",  # shipped
    "1b9ecfe83cdc259250e1a8aca174f0ad",  # canceled
    "a2e4c44360b4a57bdff22f3a4630c173",  # approved
    "bfbd0f9bdef84302105ad712db648a6c",  # no payment
]


@pytest.fixture(scope="session")
def sample_db(tmp_path_factory):
    db_file = tmp_path_factory.mktemp("db") / "test.db"
    url = f"sqlite:///{db_file.as_posix()}"
    configure_engine(url)
    import_dataset(dataset_dir=PROJECT_ROOT / "dataset", database_url=url, order_ids=SAMPLE_ORDER_IDS)
    configure_engine(url)
    yield url


@pytest.fixture
def db_session(sample_db) -> Session:
    configure_engine(sample_db)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
