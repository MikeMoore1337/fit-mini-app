from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.db.session import SessionLocal
from app.models.user import User
from app.services.jwt import decode_token, extract_bearer_token


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request.state.user = None

        raw_token = extract_bearer_token(request.headers.get("Authorization"))
        if raw_token:
            try:
                payload = decode_token(raw_token)
                if payload.get("type") == "access":
                    user_id = int(payload["sub"])
                    db = SessionLocal()
                    try:
                        user = db.query(User).filter(User.id == user_id).first()
                        request.state.user = user
                    finally:
                        db.close()
            except Exception:
                request.state.user = None

        return await call_next(request)
