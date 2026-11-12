from uuid import UUID

from flask import Blueprint, Response, current_app, jsonify, request

from asistencia.attendance_service import (
    WorkerAccessDenied,
    attendance_view,
    register_mark,
    utc_now,
)
from asistencia.http import (
    ApiError,
    database_sessions,
    require_csrf,
    session_account_id,
)

attendance_api = Blueprint("attendance", __name__, url_prefix="/api/asistencia")


def require_account() -> UUID:
    account_id = session_account_id()
    if account_id is None:
        raise ApiError(401, "Inicia sesión para continuar.", "session_required")
    return account_id


@attendance_api.get("")
def own_attendance() -> Response:
    account_id = require_account()
    with database_sessions()() as db:
        view = attendance_view(db, account_id)
    return jsonify(**view, zona_horaria=current_app.config["COMPANY_TIMEZONE"])


@attendance_api.post("/marcaciones")
def mark() -> tuple[Response, int]:
    account_id = require_account()
    require_csrf()
    data = request.get_json(silent=True)
    operation = data.get("operacion") if isinstance(data, dict) else None
    key = data.get("clave_reintento") if isinstance(data, dict) else None
    if operation not in ("entrada", "salida") or not isinstance(key, str):
        raise ApiError(400, "La operación y la clave de la marcación son obligatorias.")
    try:
        request_key = UUID(key)
    except ValueError as error:
        raise ApiError(400, "La clave de la marcación es inválida.") from error

    with database_sessions().begin() as db:
        result = register_mark(db, account_id, operation, request_key, utc_now)
    return jsonify(**result.body), result.status


@attendance_api.errorhandler(WorkerAccessDenied)
def handle_worker_access(error: WorkerAccessDenied) -> tuple[Response, int]:
    return jsonify(error=str(error), codigo="worker_forbidden"), 403
