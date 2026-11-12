from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date
from uuid import UUID
from zoneinfo import ZoneInfo

from flask import Blueprint, Response, current_app, jsonify, request
from psycopg.errors import UniqueViolation
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from asistencia.accounts import (
    MIN_NEW_PASSWORD_LENGTH,
    PASSWORD_LENGTH_MESSAGE,
    PASSWORD_LIMIT,
    USERNAME_LIMIT,
    create_account,
)
from asistencia.attendance_service import find_open_shift
from asistencia.history import PAGE_SIZE, history_page, period_bounds
from asistencia.http import (
    ApiError,
    database_sessions,
    require_csrf,
    session_account_id,
)
from asistencia.models import Account, Site, Worker

admin_api = Blueprint("admin", __name__, url_prefix="/api/admin")
NAME_LIMIT = 120


@contextmanager
def admin_session(*, write: bool = False) -> Iterator[Session]:
    account_id = session_account_id()
    if account_id is None:
        raise ApiError(401, "Inicia sesión para continuar.", "session_required")

    with database_sessions().begin() as db:
        account = db.get(Account, account_id)
        if account is None:
            raise ApiError(401, "Inicia sesión para continuar.", "session_required")
        if account.rol != "administrador":
            raise ApiError(403, "Esta operación requiere una cuenta administrativa.")
        if write:
            require_csrf()
        yield db


def payload() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "Envía los datos del formulario.")
    return data


def required_text(data: dict, field: str, label: str, limit: int) -> str:
    raw = data.get(field)
    value = raw.strip() if isinstance(raw, str) else ""
    if not 1 <= len(value) <= limit or "\0" in value:
        raise ApiError(400, f"Ingresa {label} de hasta {limit} caracteres.")
    return value


def assigned_site_id(db: Session, data: dict) -> UUID:
    raw = data.get("sede_id")
    if not isinstance(raw, str):
        raise ApiError(400, "Selecciona una sede válida.")
    try:
        site_id = UUID(raw)
    except ValueError as error:
        raise ApiError(400, "Selecciona una sede válida.") from error
    if db.get(Site, site_id) is None:
        raise ApiError(404, "La sede seleccionada no existe.")
    return site_id


def site_view(site: Site) -> dict:
    return {"id": str(site.id), "nombre": site.nombre}


def worker_view(worker: Worker, username: str | None) -> dict:
    return {
        "id": str(worker.id),
        "nombre": worker.nombre,
        "usuario": username,
        "sede_id": str(worker.sede_id),
        "activo": worker.activo,
    }


def save_site(db: Session, site: Site, name: str) -> dict:
    site.nombre = name
    db.add(site)
    try:
        db.flush()
    except IntegrityError as error:
        if not isinstance(error.orig, UniqueViolation):
            raise
        raise ApiError(409, "Ya existe una sede con ese nombre.") from error
    return site_view(site)


@admin_api.get("")
def directory() -> Response:
    with admin_session() as db:
        sites = db.scalars(select(Site).order_by(Site.nombre, Site.id))
        workers = db.execute(
            select(Worker, Account.nombre_usuario)
            .outerjoin(Account, Account.id == Worker.cuenta_id)
            .order_by(Worker.nombre, Worker.id)
        )
        return jsonify(
            sedes=[site_view(site) for site in sites],
            trabajadores=[
                worker_view(worker, username) for worker, username in workers
            ],
        )


def history_date(field: str) -> date:
    value = request.args.get(field, "")
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
    except ValueError as error:
        raise ApiError(400, "Indica las fechas de inicio y fin del período.") from error
    return parsed


def history_id(field: str, message: str) -> UUID | None:
    value = request.args.get(field)
    if value is None:
        return None
    try:
        return UUID(value)
    except ValueError as error:
        raise ApiError(400, message) from error


@admin_api.get("/jornadas")
def attendance_history() -> Response:
    with admin_session() as db:
        timezone = current_app.config["COMPANY_TIMEZONE"]
        start, end = history_date("desde"), history_date("hasta")
        try:
            lower, upper = period_bounds(start, end, ZoneInfo(timezone))
        except ValueError as error:
            raise ApiError(400, str(error)) from error
        except OverflowError as error:
            raise ApiError(400, "Selecciona un período de fechas válido.") from error

        try:
            page = int(request.args.get("pagina", "1"))
            if page < 1 or (page - 1) * PAGE_SIZE > 2**63 - 1:
                raise ValueError
        except ValueError as error:
            raise ApiError(400, "Selecciona un número de página válido.") from error

        result = history_page(
            db,
            lower,
            upper,
            worker_id=history_id("trabajador_id", "Selecciona un trabajador válido."),
            site_id=history_id("sede_id", "Selecciona una sede válida."),
            page=page,
        )
        return jsonify(**result, zona_horaria=timezone)


@admin_api.post("/sedes")
def create_site() -> tuple[Response, int]:
    with admin_session(write=True) as db:
        name = required_text(payload(), "nombre", "el nombre de la sede", NAME_LIMIT)
        return jsonify(save_site(db, Site(), name)), 201


@admin_api.patch("/sedes/<uuid:site_id>")
def edit_site(site_id: UUID) -> Response:
    with admin_session(write=True) as db:
        name = required_text(payload(), "nombre", "el nombre de la sede", NAME_LIMIT)
        site = db.get(Site, site_id)
        if site is None:
            raise ApiError(404, "La sede no existe.")
        return jsonify(save_site(db, site, name))


@admin_api.post("/trabajadores")
def create_worker() -> tuple[Response, int]:
    with admin_session(write=True) as db:
        data = payload()
        name = required_text(data, "nombre", "el nombre del trabajador", NAME_LIMIT)
        username = required_text(
            data, "usuario", "el nombre de usuario", USERNAME_LIMIT
        )
        password = data.get("contrasena")
        if (
            not isinstance(password, str)
            or not MIN_NEW_PASSWORD_LENGTH <= len(password) <= PASSWORD_LIMIT
        ):
            raise ApiError(400, PASSWORD_LENGTH_MESSAGE)
        site_id = assigned_site_id(db, data)
        account = create_account(
            db, username, generate_password_hash(password), "trabajador"
        )
        if account is None:
            raise ApiError(409, "El nombre de usuario ya está en uso.")

        worker = Worker(nombre=name, cuenta_id=account.id, sede_id=site_id)
        db.add(worker)
        db.flush()
        return jsonify(worker_view(worker, username)), 201


@admin_api.patch("/trabajadores/<uuid:worker_id>")
def edit_worker(worker_id: UUID) -> Response:
    with admin_session(write=True) as db:
        data = payload()
        name = required_text(data, "nombre", "el nombre del trabajador", NAME_LIMIT)
        site_id = assigned_site_id(db, data)
        worker = db.get(Worker, worker_id, with_for_update=True)
        if worker is None:
            raise ApiError(404, "El trabajador no existe.")
        worker.nombre = name
        worker.sede_id = site_id
        username = db.scalar(
            select(Account.nombre_usuario).where(Account.id == worker.cuenta_id)
        )
        return jsonify(worker_view(worker, username))


@admin_api.post("/trabajadores/<uuid:worker_id>/desactivar")
def deactivate_worker(worker_id: UUID) -> Response:
    with admin_session(write=True) as db:
        # Usa el mismo bloqueo que la marcación para decidir sobre la jornada abierta.
        worker = db.get(Worker, worker_id, with_for_update=True)
        if worker is None:
            raise ApiError(404, "El trabajador no existe.")
        if find_open_shift(db, worker.id) is not None:
            raise ApiError(
                409,
                "El trabajador debe registrar su salida antes de desactivarlo.",
                "open_shift",
            )
        worker.activo = False
        username = db.scalar(
            select(Account.nombre_usuario).where(Account.id == worker.cuenta_id)
        )
        return jsonify(worker_view(worker, username))
