import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient

_TEST_DB = Path(tempfile.gettempdir()) / "fitmini_pytest.db"
_TEST_DATABASE_URL = os.environ.get("TEST_DATABASE_URL") or f"sqlite:///{_TEST_DB.as_posix()}"
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("APP_NAME", "FitMiniApp Test")
os.environ.setdefault("APP_HOST", "127.0.0.1")
os.environ.setdefault("APP_PORT", "8000")
os.environ.setdefault("APP_DEBUG", "false")
os.environ.setdefault("SECRET_KEY", "test-secret-key-at-least-thirty-two-characters")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_DAYS", "30")
os.environ["DATABASE_URL"] = _TEST_DATABASE_URL
os.environ.setdefault("ENABLE_DEV_AUTH", "true")
os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test-token")
os.environ.setdefault("BOT_INTERNAL_TOKEN", "test-token")
os.environ.setdefault("FRONTEND_BASE_URL", "https://app.your-fitness-coach.ru")
os.environ.setdefault("PAYMENT_PUBLIC_URL", "https://app.your-fitness-coach.ru")

from fitminiapp_api.core.rate_limit import limiter
from fitminiapp_api.db.base import Base
from fitminiapp_api.db.session import engine, get_session_context
from fitminiapp_api.main import app
from fitminiapp_api.services.seed import seed_demo_data


@pytest.fixture(autouse=True)
def reset_db():
    limiter.reset()
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
