from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, time, timedelta
from typing import Literal
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from asistencia.models import Account, MarkRequest, Shift, Site, Worker

Operation = Literal["entrada", "salida"]


class WorkerAccessDenied(Exception):
    pass


@dataclass(frozen=True)
class MarkOutcome:
    body: dict
    status: int = 200


def utc_now() -> datetime:
    return datetime.now(UTC)


def day_bounds(instant: datetime, timezone: ZoneInfo) -> tuple[datetime, datetime]:
    day = instant.astimezone(timezone).date()
    return (
        datetime.combine(day, time.min, timezone).astimezone(UTC),
        datetime.combine(day + timedelta(days=1), time.min, timezone).astimezone(UTC),
    )


def get_worker(db: Session, account_id: UUID, *, lock: bool = False) -> Worker:
    query = (
        select(Worker)
        .join(Account, Account.id == Worker.cuenta_id)
        .where(Worker.cuenta_id == account_id, Account.rol == "trabajador")
    )
    if lock:
        query = query.with_for_update(of=Worker)
    worker = db.scalar(query)
    if worker is None:
        raise WorkerAccessDenied(
            "Esta cuenta no tiene acceso a la asistencia personal."
        )
    return worker


def shift_details(shift: Shift, site_name: str, day_start: datetime) -> dict:
    entry = shift.entrada.astimezone(UTC)
    exit_time = shift.salida.astimezone(UTC) if shift.salida is not None else None
    return {
        "id": str(shift.id),
        "sede": site_name,
        "entrada": entry.isoformat(),
        "salida": exit_time.isoformat() if exit_time is not None else None,
        "tiene_foto_entrada": shift.foto_entrada is not None,
        "tiene_foto_salida": shift.foto_salida is not None,
        "estado": (
            "cerrada"
            if exit_time is not None
            else "sin_salida"
            if shift.sin_salida or entry < day_start
            else "abierta"
        ),
        "duracion_segundos": (
            int((exit_time - entry).total_seconds()) if exit_time is not None else None
        ),
    }


def attendance_view(
    db: Session, account_id: UUID, instant: datetime, timezone: ZoneInfo
) -> dict:
    day_start, next_day = day_bounds(instant, timezone)
    worker = get_worker(db, account_id)
    current_site = db.get_one(Site, worker.sede_id)
    rows = db.execute(
        select(Shift, Site.nombre)
        .join(Site, Site.id == Shift.sede_id)
        .where(Shift.trabajador_id == worker.id)
        .order_by(Shift.entrada.desc(), Shift.id.desc())
    )
    shifts = []
    today = None
    open_shift = None
    for shift, site_name in rows:
        details = shift_details(shift, site_name, day_start)
        shifts.append(details)
        if day_start <= shift.entrada < next_day:
            if today is None:
                today = details
            if details["estado"] == "abierta":
                open_shift = details
    return {
        "nombre": worker.nombre,
        "sede": current_site.nombre,
        "activo": worker.activo,
        "jornada_abierta": open_shift,
        "jornada_hoy": today,
        "actualizar_en_ms": int((next_day - instant).total_seconds() * 1000),
        "jornadas": shifts,
    }


def conflict(message: str) -> MarkOutcome:
    return MarkOutcome({"error": message, "codigo": "attendance_conflict"}, 409)


def current_open_shift(
    db: Session, worker_id: UUID, day_start: datetime
) -> Shift | None:
    # El llamador ya tiene bloqueada la fila del trabajador.
    shift = db.scalar(
        select(Shift).where(
            Shift.trabajador_id == worker_id, Shift.salida.is_(None), ~Shift.sin_salida
        )
    )
    if shift is not None and shift.entrada < day_start:
        shift.sin_salida = True
        db.flush()
        return None
    return shift


def apply_mark(
    db: Session,
    worker: Worker,
    operation: Operation,
    clock: Callable[[], datetime],
    timezone: ZoneInfo,
    *,
    expected_shift_id: UUID | None,
    save_photo: Callable[[], str] | None,
) -> tuple[Shift | None, MarkOutcome]:
    if not worker.activo:
        return None, MarkOutcome(
            {"error": "El trabajador está desactivado.", "codigo": "worker_forbidden"},
            403,
        )

    if operation == "salida" and expected_shift_id is None:
        return None, MarkOutcome(
            {
                "error": "Actualiza la página antes de volver a registrar la salida.",
                "codigo": "request_rejected",
            },
            400,
        )

    instant = clock()
    day_start, next_day = day_bounds(instant, timezone)
    shift = current_open_shift(db, worker.id, day_start)
    if operation == "entrada":
        if shift is not None:
            return None, conflict("Ya tienes una jornada abierta.")
        if (
            db.scalar(
                select(Shift.id)
                .where(
                    Shift.trabajador_id == worker.id,
                    Shift.entrada >= day_start,
                    Shift.entrada < next_day,
                )
                .limit(1)
            )
            is not None
        ):
            return None, conflict("Ya registraste tu asistencia de hoy.")
        shift = Shift(
            trabajador_id=worker.id,
            sede_id=worker.sede_id,
            entrada=instant,
            foto_entrada=save_photo() if save_photo else None,
        )
        db.add(shift)
        db.flush()
    else:
        if shift is None:
            return None, conflict("No tienes una jornada abierta de hoy para cerrar.")
        if shift.id != expected_shift_id:
            return None, conflict(
                "Esa jornada ya se cerró. Revisa tu asistencia y vuelve a marcar."
            )
        if instant < shift.entrada:
            return None, conflict("La hora de salida es anterior a la entrada.")
        if save_photo:
            shift.foto_salida = save_photo()
        shift.salida = instant

    site = db.get_one(Site, shift.sede_id)
    return shift, MarkOutcome(
        {
            "operacion": operation,
            "jornada": shift_details(shift, site.nombre, day_start),
        }
    )


def register_mark(
    db: Session,
    account_id: UUID,
    operation: Operation,
    request_key: UUID,
    clock: Callable[[], datetime],
    timezone: ZoneInfo,
    *,
    expected_shift_id: UUID | None,
    save_photo: Callable[[], str] | None = None,
) -> MarkOutcome:
    # Serializa las marcaciones de este trabajador hasta confirmar la transacción.
    worker = get_worker(db, account_id, lock=True)
    previous = db.get(MarkRequest, (account_id, request_key))
    if previous is not None:
        if previous.operacion != operation:
            return conflict("La solicitud ya se usó para otra operación.")
        if (
            expected_shift_id is not None
            and previous.jornada_id is not None
            and expected_shift_id != previous.jornada_id
        ):
            return conflict("La solicitud ya se usó para otra jornada.")
        # Los reintentos antiguos sin jornada aún pueden recuperar su resultado.
        return MarkOutcome(previous.resultado, previous.estado_http)

    shift, outcome = apply_mark(
        db,
        worker,
        operation,
        clock,
        timezone,
        expected_shift_id=expected_shift_id,
        save_photo=save_photo,
    )
    db.add(
        MarkRequest(
            cuenta_id=account_id,
            clave_reintento=request_key,
            jornada_id=shift.id if shift else None,
            operacion=operation,
            estado_http=outcome.status,
            resultado=outcome.body,
        )
    )
    return outcome
