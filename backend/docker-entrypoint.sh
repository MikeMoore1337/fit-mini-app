#!/usr/bin/env bash
set -e
python - <<'PY'
import time
from sqlalchemy import create_engine, text
from app.core.config import settings

for attempt in range(60):
    try:
        engine = create_engine(settings.database_url, future=True)
        with engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        print('Database is ready')
        break
    except Exception as exc:
        print(f'Waiting for database ({attempt + 1}/60): {exc}')
        time.sleep(2)
else:
    raise SystemExit('Database did not become ready in time')
PY
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'
