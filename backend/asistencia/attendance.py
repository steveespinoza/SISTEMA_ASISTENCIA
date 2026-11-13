from uuid import UUID
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, current_app, jsonify, redirect, request
from sqlalchemy import select
from werkzeug.exceptions import RequestEntityTooLarge

from asistencia.attendance_service import (
    WorkerAccessDenied,
    attendance_view,
    register_mark,
    utc_now,
)
from asistencia.evidence import InvalidPhoto, PhotoStorageUnavailable
from asistencia.http import (
    ApiError,
    database_sessions,
    require_csrf,
    session_account_id,
)
from asistencia.models import Account, Shift, Worker

attendance_api = Blueprint("attendance", __name__, url_prefix="/api/asistencia")


def require_account() -> UUID:
    account_id = session_account_id()
    if account_id is None:
        raise ApiError(401, "Inicia sesión para continuar.", "session_required")
    return account_id


@attendance_api.get("")
def own_attendance() -> Response:
    account_id = require_account()
    timezone = current_app.config["COMPANY_TIMEZONE"]
    with database_sessions()() as db:
        view = attendance_view(db, account_id, utc_now(), ZoneInfo(timezone))
    return jsonify(
        **view,
        zona_horaria=timezone,
        requiere_foto="photo_storage" in current_app.extensions,
    )


@attendance_api.post("/marcaciones")
def mark() -> tuple[Response, int]:
    account_id = require_account()
    require_csrf()
    storage = current_app.extensions.get("photo_storage")
    photo = None
    if request.mimetype == "multipart/form-data":
        if storage is None:
            raise ApiError(400, "La marcación con foto no está habilitada.")
        request.max_content_length = current_app.config["PHOTO_REQUEST_LIMIT"]
        request.max_form_parts = 4
        data = request.form.to_dict()
        photo = request.files.get("foto")
        if len(request.files.getlist("foto")) > 1:
            raise ApiError(400, "Envía una sola foto.", "invalid_photo")
    else:
        data = request.get_json(silent=True)
    operation = data.get("operacion") if isinstance(data, dict) else None
    key = data.get("clave_reintento") if isinstance(data, dict) else None
    if operation not in ("entrada", "salida") or not isinstance(key, str):
        raise ApiError(400, "La operación y la clave de la marcación son obligatorias.")
    try:
        request_key = UUID(key)
    except ValueError as error:
        raise ApiError(400, "La clave de la marcación es inválida.") from error

    expected_shift_id = None
    if operation == "salida" and "jornada_id" in data:
        shift_id = data["jornada_id"]
        if not isinstance(shift_id, str):
            raise ApiError(400, "El identificador de la jornada es inválido.")
        try:
            expected_shift_id = UUID(shift_id)
        except ValueError as error:
            raise ApiError(
                400, "El identificador de la jornada es inválido."
            ) from error

    def save_photo() -> str:
        if photo is None:
            raise ApiError(
                400, "Agrega una foto para registrar la marcación.", "photo_required"
            )
        try:
            return storage.save(account_id, request_key, photo)
        except InvalidPhoto as error:
            raise ApiError(400, str(error), "invalid_photo") from error

    with database_sessions().begin() as db:
        result = register_mark(
            db,
            account_id,
            operation,
            request_key,
            utc_now,
            ZoneInfo(current_app.config["COMPANY_TIMEZONE"]),
            expected_shift_id=expected_shift_id,
            save_photo=save_photo if storage is not None else None,
        )
    return jsonify(**result.body), result.status


@attendance_api.get("/jornadas/<uuid:shift_id>/fotos/<operation>")
def view_photo(shift_id: UUID, operation: str) -> Response:
    account_id = require_account()
    if operation not in ("entrada", "salida"):
        raise ApiError(404, "No se encontró la foto.")

    with database_sessions()() as db:
        account = db.get(Account, account_id)
        if account is None:
            raise ApiError(401, "Inicia sesión para continuar.", "session_required")
        column = Shift.foto_entrada if operation == "entrada" else Shift.foto_salida
        query = select(column).where(Shift.id == shift_id)
        if account.rol != "administrador":
            query = query.join(Worker, Worker.id == Shift.trabajador_id).where(
                Worker.cuenta_id == account_id
            )
        key = db.scalar(query)
    if key is None:
        raise ApiError(404, "No se encontró la foto.")
    storage = current_app.extensions.get("photo_storage")
    if storage is None:
        raise PhotoStorageUnavailable
    response = redirect(storage.access_url(key))
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


@attendance_api.errorhandler(RequestEntityTooLarge)
def handle_photo_request_size(_error: RequestEntityTooLarge) -> tuple[Response, int]:
    return jsonify(
        error="Envía una sola foto de hasta 12 MB.", codigo="invalid_photo"
    ), 413


@attendance_api.errorhandler(WorkerAccessDenied)
def handle_worker_access(error: WorkerAccessDenied) -> tuple[Response, int]:
    return jsonify(error=str(error), codigo="worker_forbidden"), 403
