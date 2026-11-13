from datetime import UTC, date, datetime, time, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from asistencia.attendance_service import shift_details
from asistencia.models import Shift, Site, Worker

PAGE_SIZE = 50


def period_bounds(
    start: date, end: date, timezone: ZoneInfo
) -> tuple[datetime, datetime]:
    if start > end:
        raise ValueError(
            "La fecha final debe ser igual o posterior a la fecha inicial."
        )

    lower = datetime.combine(start, time.min, timezone)
    upper = datetime.combine(end + timedelta(days=1), time.min, timezone)
    return lower.astimezone(UTC), upper.astimezone(UTC)


def history_page(
    db: Session,
    lower: datetime,
    upper: datetime,
    *,
    day_start: datetime,
    worker_id: UUID | None,
    site_id: UUID | None,
    page: int,
) -> dict:
    query = (
        select(Shift, Worker.nombre, Site.nombre)
        .join(Worker, Worker.id == Shift.trabajador_id)
        .join(Site, Site.id == Shift.sede_id)
        .where(Shift.entrada >= lower, Shift.entrada < upper)
    )
    if worker_id is not None:
        query = query.where(Shift.trabajador_id == worker_id)
    if site_id is not None:
        query = query.where(Shift.sede_id == site_id)
    rows = db.execute(
        query.order_by(Shift.entrada.desc(), Shift.id.desc())
        .offset((page - 1) * PAGE_SIZE)
        .limit(PAGE_SIZE + 1)
    ).all()
    return {
        "jornadas": [
            {
                **shift_details(shift, site, day_start),
                "trabajador": worker,
                "trabajador_id": str(shift.trabajador_id),
                "sede_id": str(shift.sede_id),
            }
            for shift, worker, site in rows[:PAGE_SIZE]
        ],
        "pagina": page,
        "hay_siguiente": len(rows) > PAGE_SIZE,
    }
