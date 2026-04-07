from __future__ import annotations

from app.db.session import SessionLocal
from app.models.user import User
from app.services.security import AuthError, decode_token
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request.state.user = None

        auth_header = request.headers.get("Authorization", "").strip()
        if not auth_header:
            return await call_next(request)

        parts = auth_header.split(" ", 1)
        if len(parts) != 2 or parts[0].lower() != "bearer" or not parts[1].strip():
            return await call_next(request)

        token = parts[1].strip()

        try:
            payload = decode_token(token, expected_type="access")
            user_id_raw = payload.get("sub")
            if not user_id_raw:
                return await call_next(request)

            user_id = int(user_id_raw)
        except (AuthError, ValueError, TypeError):
            return await call_next(request)

        db = SessionLocal()
        try:
            user = db.query(User).filter(User.id == user_id, User.is_active.is_(True)).first()
            request.state.user = user
        finally:
            db.close()

        return await call_next(request)
