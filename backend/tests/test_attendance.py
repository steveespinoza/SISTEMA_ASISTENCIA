import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Barrier
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash

from asistencia import attendance, create_app
from asistencia.models import Account, MarkRequest, Shift, Site, Worker

TEST_PASSWORD = "contrasena-ficticia-para-pruebas"
TEST_SECRET = "clave-ficticia-exclusiva-de-las-pruebas"


@dataclass(frozen=True)
class Sample:
    username: str
    worker_id: UUID
    site_id: UUID
    next_site_id: UUID
    other_username: str
    other_worker_id: UUID
    admin_username: str


@pytest.fixture
def app(monkeypatch):
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Define TEST_DATABASE_URL con una base PostgreSQL descartable.")

    monkeypatch.setenv("COMPANY_TIMEZONE", "America/Lima")
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "1")
    app = create_app(database_url, secret_key=TEST_SECRET)
    app.config.update(TESTING=True, PREFERRED_URL_SCHEME="https")
    yield app
    app.extensions["database_engine"].dispose()


@pytest.fixture
def sample(app):
    sessions = app.extensions["database_sessions"]
    suffix = uuid4().hex[:12]
    password_hash = generate_password_hash(TEST_PASSWORD)
    with sessions.begin() as db:
        accounts = [
            Account(
                nombre_usuario=f"{name}-{suffix}",
                hash_contrasena=password_hash,
                rol=role,
            )
            for name, role in [
                ("uno", "trabajador"),
                ("dos", "trabajador"),
                ("admin", "administrador"),
            ]
        ]
        site = Site(nombre=f"Sede inicial {suffix}")
        next_site = Site(nombre=f"Sede nueva {suffix}")
        db.add_all([*accounts, site, next_site])
        db.flush()
        workers = [
            Worker(cuenta_id=account.id, sede_id=site.id, nombre=account.nombre_usuario)
            for account in accounts[:2]
        ]
        db.add_all(workers)
        db.flush()
        account_ids = [account.id for account in accounts]
        worker_ids = [worker.id for worker in workers]
        site_ids = [site.id, next_site.id]
        sample = Sample(
            accounts[0].nombre_usuario,
            worker_ids[0],
            site_ids[0],
            site_ids[1],
            accounts[1].nombre_usuario,
            worker_ids[1],
            accounts[2].nombre_usuario,
        )

    yield sample

    with sessions.begin() as db:
        db.execute(delete(MarkRequest).where(MarkRequest.cuenta_id.in_(account_ids)))
        db.execute(delete(Shift).where(Shift.trabajador_id.in_(worker_ids)))
        db.execute(delete(Worker).where(Worker.id.in_(worker_ids)))
        db.execute(delete(Account).where(Account.id.in_(account_ids)))
        db.execute(delete(Site).where(Site.id.in_(site_ids)))


def login(client, username):
    bootstrap = client.get("/api/auth/sesion").get_json()
    response = client.post(
        "/api/auth/iniciar-sesion",
        json={"usuario": username, "contrasena": TEST_PASSWORD},
        headers={"X-CSRF-Token": bootstrap["csrf_token"]},
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["usuario"]["usuario"] == username
    assert payload["csrf_token"] != bootstrap["csrf_token"]
    return payload["csrf_token"]


def mark(client, token, operation, key=None, **extras):
    return client.post(
        "/api/asistencia/marcaciones",
        json={"operacion": operation, "clave_reintento": str(key or uuid4()), **extras},
        headers={"X-CSRF-Token": token},
    )


def test_session_credentials_and_csrf(app, sample):
    client = app.test_client()
    assert client.get("/api/asistencia").status_code == 401
    initial = client.get("/api/auth/sesion")
    cookie = initial.headers["Set-Cookie"]
    assert all(flag in cookie for flag in ("Secure", "HttpOnly", "SameSite=Lax"))
    token = initial.get_json()["csrf_token"]
    body = {"usuario": sample.username, "contrasena": TEST_PASSWORD}
    assert client.post("/api/auth/iniciar-sesion", json=body).status_code == 403

    invalid = client.post(
        "/api/auth/iniciar-sesion",
        json={**body, "contrasena": "incorrecta"},
        headers={"X-CSRF-Token": token},
    )
    assert invalid.status_code == 401
    assert invalid.get_json()["codigo"] == "login_failed"

    auth_token = login(client, sample.username)
    assert mark(client, token, "entrada").status_code == 403
    assert (
        client.post(
            "/api/auth/cerrar-sesion", headers={"X-CSRF-Token": auth_token}
        ).status_code
        == 200
    )
    assert client.get("/api/asistencia").status_code == 401


def test_shift_closes_after_midnight_and_replays_original_confirmation(
    app, sample, monkeypatch
):
    client = app.test_client()
    token = login(client, sample.username)
    early_exit_key = uuid4()
    rejected = mark(client, token, "salida", early_exit_key)
    assert rejected.status_code == 409

    # En Lima son las 22:00 y las 06:00 del día siguiente.
    start = datetime(2026, 11, 13, 3, tzinfo=UTC)
    end = datetime(2026, 11, 13, 11, tzinfo=UTC)
    entry_key, exit_key = uuid4(), uuid4()
    monkeypatch.setattr(attendance, "utc_now", lambda: start)
    entry = mark(client, token, "entrada", entry_key, entrada="2000-01-01T00:00:00Z")
    assert entry.status_code == 200
    original = entry.get_json()
    assert original["jornada"]["entrada"] == start.isoformat()
    assert original["jornada"]["salida"] is None
    retry = mark(client, token, "salida", early_exit_key)
    assert retry.status_code == 409
    assert retry.get_json() == rejected.get_json()

    with app.extensions["database_sessions"].begin() as db:
        db.get_one(Worker, sample.worker_id).sede_id = sample.next_site_id

    monkeypatch.setattr(attendance, "utc_now", lambda: end)
    exit_response = mark(client, token, "salida", exit_key)
    assert exit_response.status_code == 200
    closed = exit_response.get_json()
    assert closed["jornada"]["id"] == original["jornada"]["id"]
    assert closed["jornada"]["sede"] == original["jornada"]["sede"]
    assert closed["jornada"]["salida"] == end.isoformat()
    assert closed["jornada"]["duracion_segundos"] == 8 * 60 * 60
    assert mark(client, token, "salida", exit_key).get_json() == closed
    assert mark(client, token, "entrada", entry_key).get_json() == original
    assert mark(client, token, "salida", entry_key).status_code == 409

    history = client.get("/api/asistencia").get_json()
    assert history["zona_horaria"] == "America/Lima"
    assert history["jornada_abierta"] is None
    assert history["jornadas"] == [closed["jornada"]]
    assert history["sede"] != closed["jornada"]["sede"]


def test_history_is_private_and_admin_cannot_mark(app, sample):
    other = app.test_client()
    other_token = login(other, sample.other_username)
    assert mark(other, other_token, "entrada").status_code == 200

    client = app.test_client()
    token = login(client, sample.username)
    spoofed = client.get(f"/api/asistencia?trabajador_id={sample.other_worker_id}")
    assert spoofed.get_json()["jornadas"] == []

    admin = app.test_client()
    admin_token = login(admin, sample.admin_username)
    assert admin.get("/api/asistencia").status_code == 403
    assert mark(admin, admin_token, "entrada").status_code == 403

    with app.extensions["database_sessions"].begin() as db:
        db.get_one(Worker, sample.worker_id).activo = False
    assert mark(client, token, "entrada").status_code == 403


@pytest.mark.parametrize("same_key", [False, True])
def test_concurrent_entries_leave_one_shift(app, sample, same_key):
    barrier = Barrier(2)
    first_key = uuid4()
    second_key = first_key if same_key else uuid4()

    def enter(key):
        client = app.test_client()
        token = login(client, sample.username)
        barrier.wait(timeout=10)
        return mark(client, token, "entrada", key)

    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(enter, [first_key, second_key]))

    expected = [200, 200] if same_key else [200, 409]
    assert sorted(response.status_code for response in responses) == expected
    if same_key:
        assert responses[0].get_json() == responses[1].get_json()

    sessions = app.extensions["database_sessions"]
    with sessions() as db:
        count = db.scalar(
            select(func.count())
            .select_from(Shift)
            .where(Shift.trabajador_id == sample.worker_id, Shift.salida.is_(None))
        )
        assert count == 1

    with pytest.raises(IntegrityError), sessions.begin() as db:
        db.add(
            Shift(
                trabajador_id=sample.worker_id,
                sede_id=sample.site_id,
                entrada=datetime.now(UTC),
            )
        )
