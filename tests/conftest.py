import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient

_TEST_DB = Path(tempfile.gettempdir()) / "fitmini_pytest.db"
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("APP_NAME", "FitMiniApp Test")
os.environ.setdefault("APP_HOST", "127.0.0.1")
os.environ.setdefault("APP_PORT", "8000")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "30")
os.environ["DATABASE_URL"] = f"sqlite:///{_TEST_DB.as_posix()}"
os.environ.setdefault("ENABLE_DEV_AUTH", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("FRONTEND_BASE_URL", "https://app.your-fitness-coach.ru")
os.environ.setdefault("PAYMENT_PUBLIC_URL", "https://app.your-fitness-coach.ru")

from app.db.base import Base
from app.db.session import engine, get_session_context
from app.main import app
from app.services.seed import seed_demo_data


@pytest.fixture(autouse=True)
def reset_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with get_session_context() as session:
        seed_demo_data(session)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture()
def client():
    return TestClient(app)
