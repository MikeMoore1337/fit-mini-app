import os

# Bot settings read `.env` at import time. Explicit test environment values keep local
# credentials and administrator identifiers out of test objects, failures, and snapshots.
os.environ["TELEGRAM_BOT_TOKEN"] = "test-token"
os.environ["BOT_INTERNAL_TOKEN"] = "test-bot-internal-token"
os.environ["BACKEND_INTERNAL_URL"] = "http://backend.test:8000"
os.environ["FRONTEND_BASE_URL"] = "https://app.your-fitness-coach.ru"
os.environ["ADMIN_TELEGRAM_USER_IDS"] = "7001"
os.environ["SUPPORT_BOT_TOKEN"] = "legacy-redirect-test-token"
os.environ["SUPPORT_BOT_ENABLED"] = "false"
