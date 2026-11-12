from secrets import compare_digest, token_urlsafe
from uuid import UUID

from flask import current_app, request, session
from sqlalchemy.orm import sessionmaker


class ApiError(Exception):
    def __init__(
        self, status: int, message: str, code: str = "request_rejected"
    ) -> None:
        super().__init__(message)
        self.status = status
        self.message = message
        self.code = code


def database_sessions() -> sessionmaker:
    return current_app.extensions["database_sessions"]


def session_account_id() -> UUID | None:
    account_id = session.get("cuenta_id")
    return UUID(account_id) if account_id else None


def csrf_token() -> str:
    token = session.get("csrf_token")
    if token is None:
        token = token_urlsafe(32)
        session["csrf_token"] = token
    return token


def require_csrf() -> None:
    expected = session.get("csrf_token")
    received = request.headers.get("X-CSRF-Token", "")
    if not expected or not compare_digest(expected.encode(), received.encode()):
        raise ApiError(403, "Actualiza la página para continuar.", "csrf_invalid")
