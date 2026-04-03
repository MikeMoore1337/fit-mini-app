import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

import pytest
from fastapi.testclient import TestClient

os.environ['DATABASE_URL'] = 'sqlite:///./test_fitminiapp.db'
os.environ['ENABLE_DEV_AUTH'] = 'true'
os.environ['TELEGRAM_BOT_TOKEN'] = 'test-token'
os.environ['SECRET_KEY'] = 'test-secret'

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
    db_file = Path('test_fitminiapp.db')
    if db_file.exists():
        db_file.unlink()


@pytest.fixture()
def client():
    return TestClient(app)