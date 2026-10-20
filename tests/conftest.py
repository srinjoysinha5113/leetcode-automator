import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import app.database as db_module
from app.config import settings
from app.models import Base

@pytest.fixture(autouse=True, scope="session")
def isolate_test_database():
    """Points database operations during tests to an isolated test database so production DB is never touched."""
    test_db_path = settings.DATA_DIR / "test_suite.db"
    test_url = f"sqlite:///{test_db_path}"

    test_engine = create_engine(
        test_url,
        echo=False,
        connect_args={"check_same_thread": False}
    )
    test_sessionmaker = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
        expire_on_commit=False
    )

    # Rebind app.database globals to test engine
    orig_engine = db_module.engine
    orig_sessionmaker = db_module.SessionLocal
    db_module.engine = test_engine
    db_module.SessionLocal = test_sessionmaker

    Base.metadata.create_all(bind=test_engine)

    yield

    # Restore originals
    db_module.engine = orig_engine
    db_module.SessionLocal = orig_sessionmaker

    if test_db_path.exists():
        try:
            test_db_path.unlink()
        except Exception:
            pass
