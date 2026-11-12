from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID

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


def shift_details(shift: Shift, site_name: str) -> dict:
    return {
        "id": str(shift.id),
        "sede": site_name,
        "entrada": shift.entrada.astimezone(UTC).isoformat(),
        "salida": shift.salida.astimezone(UTC).isoformat() if shift.salida else None,
        "duracion_segundos": (
            int((shift.salida - shift.entrada).total_seconds())
            if shift.salida
            else None
        ),
    }


def attendance_view(db: Session, account_id: UUID) -> dict:
    worker = get_worker(db, account_id)
    current_site = db.get_one(Site, worker.sede_id)
    rows = db.execute(
        select(Shift, Site.nombre)
        .join(Site, Site.id == Shift.sede_id)
        .where(Shift.trabajador_id == worker.id)
        .order_by(Shift.entrada.desc(), Shift.id.desc())
    )
    shifts = [shift_details(shift, site_name) for shift, site_name in rows]
    open_shift = next((shift for shift in shifts if shift["salida"] is None), None)
    return {
        "nombre": worker.nombre,
        "sede": current_site.nombre,
        "activo": worker.activo,
        "jornada_abierta": open_shift,
        "jornadas": shifts,
    }


def conflict(message: str) -> MarkOutcome:
    return MarkOutcome({"error": message, "codigo": "attendance_conflict"}, 409)


def apply_mark(
    db: Session, worker: Worker, operation: Operation, clock: Callable[[], datetime]
) -> tuple[Shift | None, MarkOutcome]:
    if not worker.activo:
        return None, MarkOutcome(
            {"error": "El trabajador está desactivado.", "codigo": "worker_forbidden"},
            403,
        )

    shift = db.scalar(
        select(Shift).where(Shift.trabajador_id == worker.id, Shift.salida.is_(None))
    )
    instant = clock()
    if operation == "entrada":
        if shift is not None:
            return None, conflict("Ya tienes una jornada abierta.")
        shift = Shift(trabajador_id=worker.id, sede_id=worker.sede_id, entrada=instant)
        db.add(shift)
        db.flush()
    else:
        if shift is None:
            return None, conflict("No tienes una jornada abierta para cerrar.")
        if instant < shift.entrada:
            return None, conflict("La hora de salida es anterior a la entrada.")
        shift.salida = instant

    site = db.get_one(Site, shift.sede_id)
    return shift, MarkOutcome(
        {"operacion": operation, "jornada": shift_details(shift, site.nombre)}
    )


def register_mark(
    db: Session,
    account_id: UUID,
    operation: Operation,
    request_key: UUID,
    clock: Callable[[], datetime],
) -> MarkOutcome:
    # Serializa las marcaciones de este trabajador hasta confirmar la transacción.
    worker = get_worker(db, account_id, lock=True)
    previous = db.get(MarkRequest, (account_id, request_key))
    if previous is not None:
        if previous.operacion != operation:
            return conflict("La solicitud ya se usó para otra operación.")
        return MarkOutcome(previous.resultado, previous.estado_http)

    shift, outcome = apply_mark(db, worker, operation, clock)
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
