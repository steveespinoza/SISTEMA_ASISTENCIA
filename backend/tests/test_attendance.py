import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import Barrier, Event
from time import monotonic, sleep
from uuid import UUID, uuid4

import pytest
from sqlalchemy import delete, func, select, text
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
    unknown_shift_id = str(uuid4())
    rejected = mark(
        client, token, "salida", early_exit_key, jornada_id=unknown_shift_id
    )
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
    retry = mark(client, token, "salida", early_exit_key, jornada_id=unknown_shift_id)
    assert retry.status_code == 409
    assert retry.get_json() == rejected.get_json()

    with app.extensions["database_sessions"].begin() as db:
        db.get_one(Worker, sample.worker_id).sede_id = sample.next_site_id

    monkeypatch.setattr(attendance, "utc_now", lambda: end)
    shift_id = original["jornada"]["id"]
    exit_response = mark(client, token, "salida", exit_key, jornada_id=shift_id)
    assert exit_response.status_code == 200
    closed = exit_response.get_json()
    assert closed["jornada"]["id"] == original["jornada"]["id"]
    assert closed["jornada"]["sede"] == original["jornada"]["sede"]
    assert closed["jornada"]["salida"] == end.isoformat()
    assert closed["jornada"]["duracion_segundos"] == 8 * 60 * 60
    assert (
        mark(client, token, "salida", exit_key, jornada_id=shift_id).get_json()
        == closed
    )
    assert mark(client, token, "entrada", entry_key).get_json() == original
    assert (
        mark(client, token, "salida", entry_key, jornada_id=shift_id).status_code == 409
    )

    history = client.get("/api/asistencia").get_json()
    assert history["zona_horaria"] == "America/Lima"
    assert history["jornada_abierta"] is None
    assert history["jornadas"] == [closed["jornada"]]
    assert history["sede"] != closed["jornada"]["sede"]


def test_stale_exit_cannot_close_a_new_shift(app, sample, monkeypatch):
    first_client, stale_client = app.test_client(), app.test_client()
    first_token = login(first_client, sample.username)
    stale_token = login(stale_client, sample.username)
    monkeypatch.setattr(
        attendance, "utc_now", lambda: datetime(2026, 11, 13, 11, tzinfo=UTC)
    )

    first_entry = mark(first_client, first_token, "entrada")
    assert first_entry.status_code == 200
    first_id = stale_client.get("/api/asistencia").json["jornada_abierta"]["id"]
    assert first_id == first_entry.json["jornada"]["id"]

    first_exit_key = uuid4()
    first_exit = mark(
        first_client, first_token, "salida", first_exit_key, jornada_id=first_id
    )
    assert first_exit.status_code == 200
    next_entry = mark(first_client, first_token, "entrada")
    assert next_entry.status_code == 200
    next_shift = next_entry.json["jornada"]
    assert next_shift["id"] != first_id

    stale_key = uuid4()
    stale_exit = mark(
        stale_client, stale_token, "salida", stale_key, jornada_id=first_id
    )
    assert stale_exit.status_code == 409
    assert stale_exit.json["codigo"] == "attendance_conflict"
    assert mark(
        stale_client, stale_token, "salida", stale_key, jornada_id=first_id
    ).json == (stale_exit.json)

    # Una salida antigua sin jornada solo puede recuperar un resultado registrado.
    assert (
        mark(first_client, first_token, "salida", first_exit_key).json
        == first_exit.json
    )
    assert mark(stale_client, stale_token, "salida").status_code == 400
    assert (
        mark(stale_client, stale_token, "salida", jornada_id="invalida").status_code
        == 400
    )
    wrong_retry = mark(
        first_client, first_token, "salida", first_exit_key, jornada_id=next_shift["id"]
    )
    assert wrong_retry.status_code == 409
    assert stale_client.get("/api/asistencia").json["jornada_abierta"] == next_shift

    fresh_exit = mark(stale_client, stale_token, "salida", jornada_id=next_shift["id"])
    assert fresh_exit.status_code == 200
    assert fresh_exit.json["jornada"]["id"] == next_shift["id"]


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


def test_bootstrap_creates_only_the_first_admin(app):
    username, second_username = (f"admin-{uuid4().hex}" for _ in range(2))
    runner = app.test_cli_runner()
    passwords = f"{TEST_PASSWORD}\n{TEST_PASSWORD}\n"
    sessions = app.extensions["database_sessions"]
    try:
        created = runner.invoke(
            args=["crear-administrador", "--usuario", username], input=passwords
        )
        assert created.exit_code == 0, created.output
        second = runner.invoke(
            args=["crear-administrador", "--usuario", second_username], input=passwords
        )
        assert second.exit_code == 1
        assert "Ya existe una cuenta administrativa." in second.output

        client = app.test_client()
        login(client, username)
        assert client.get("/api/admin").status_code == 200
        with sessions() as db:
            assert (
                db.scalar(
                    select(Account.id).where(Account.nombre_usuario == second_username)
                )
                is None
            )
    finally:
        with sessions.begin() as db:
            db.execute(
                delete(Account).where(
                    Account.nombre_usuario.in_([username, second_username])
                )
            )


def test_admin_manages_sites_and_worker_through_deactivation(app, sample):
    admin = app.test_client()
    assert admin.get("/api/admin").status_code == 401
    admin_token = login(admin, sample.admin_username)
    headers = {"X-CSRF-Token": admin_token}
    worker_client = app.test_client()
    worker_token = login(worker_client, sample.username)
    assert worker_client.get("/api/admin").status_code == 403
    assert (
        worker_client.post(
            "/api/admin/sedes",
            json={"nombre": "Sin permiso"},
            headers={"X-CSRF-Token": worker_token},
        ).status_code
        == 403
    )
    assert (
        admin.post("/api/admin/sedes", json={"nombre": "Sin CSRF"}).status_code == 403
    )

    suffix = uuid4().hex[:12]
    site_name, renamed = f"Sede {suffix}", f"Sede principal {suffix}"
    username = f"nuevo-{suffix}"
    worker_data = {
        "nombre": "Trabajadora de prueba",
        "usuario": username,
        "contrasena": TEST_PASSWORD,
    }
    sessions = app.extensions["database_sessions"]
    try:
        assert (
            admin.post(
                "/api/admin/sedes", headers=headers, json={"nombre": " "}
            ).status_code
            == 400
        )
        created_site = admin.post(
            "/api/admin/sedes", headers=headers, json={"nombre": site_name}
        )
        assert created_site.status_code == 201
        site_id = created_site.json["id"]
        assert (
            admin.post(
                "/api/admin/sedes", headers=headers, json={"nombre": site_name}
            ).status_code
            == 409
        )
        updated_site = admin.patch(
            f"/api/admin/sedes/{site_id}", headers=headers, json={"nombre": renamed}
        )
        assert updated_site.status_code == 200
        assert updated_site.json == {"id": site_id, "nombre": renamed}

        assert (
            admin.post(
                "/api/admin/trabajadores",
                headers=headers,
                json={**worker_data, "sede_id": str(uuid4())},
            ).status_code
            == 404
        )
        created_worker = admin.post(
            "/api/admin/trabajadores",
            headers=headers,
            json={**worker_data, "sede_id": site_id},
        )
        assert created_worker.status_code == 201
        worker = created_worker.json
        assert worker == {
            "id": worker["id"],
            "nombre": worker_data["nombre"],
            "usuario": username,
            "sede_id": site_id,
            "activo": True,
        }
        worker_path = f"/api/admin/trabajadores/{worker['id']}"
        assert (
            admin.post(
                "/api/admin/trabajadores",
                headers=headers,
                json={**worker_data, "sede_id": site_id},
            ).status_code
            == 409
        )

        new_worker = app.test_client()
        token = login(new_worker, username)
        entry = mark(new_worker, token, "entrada")
        assert entry.status_code == 200
        assert entry.json["jornada"]["sede"] == renamed
        deactivate_path = worker_path + "/desactivar"
        denied = admin.post(deactivate_path, headers=headers)
        assert denied.status_code == 409
        assert denied.json["codigo"] == "open_shift"

        reassigned = admin.patch(
            worker_path,
            headers=headers,
            json={"nombre": "Nombre actualizado", "sede_id": str(sample.next_site_id)},
        )
        assert reassigned.status_code == 200
        assert reassigned.json["activo"] is True
        assert reassigned.json["nombre"] == "Nombre actualizado"
        assert reassigned.json["sede_id"] == str(sample.next_site_id)
        first_exit = mark(
            new_worker, token, "salida", jornada_id=entry.json["jornada"]["id"]
        )
        assert first_exit.status_code == 200
        assert first_exit.json["jornada"]["sede"] == renamed

        next_entry = mark(new_worker, token, "entrada")
        assert next_entry.status_code == 200
        assert next_entry.json["jornada"]["sede"] != renamed
        assert (
            mark(
                new_worker, token, "salida", jornada_id=next_entry.json["jornada"]["id"]
            ).status_code
            == 200
        )
        deactivated = admin.post(deactivate_path, headers=headers)
        assert deactivated.status_code == 200
        assert deactivated.json["activo"] is False
        assert admin.post(deactivate_path, headers=headers).json == deactivated.json
        assert mark(new_worker, token, "entrada").status_code == 403
        history = new_worker.get("/api/asistencia").json
        assert history["activo"] is False
        assert history["jornada_abierta"] is None
        assert len(history["jornadas"]) == 2
        assert first_exit.json["jornada"] in history["jornadas"]
        directory = admin.get("/api/admin").json
        assert updated_site.json in directory["sedes"]
        assert deactivated.json in directory["trabajadores"]
    finally:
        with sessions.begin() as db:
            accounts = select(Account.id).where(Account.nombre_usuario == username)
            workers = select(Worker.id).where(Worker.cuenta_id.in_(accounts))
            db.execute(delete(MarkRequest).where(MarkRequest.cuenta_id.in_(accounts)))
            db.execute(delete(Shift).where(Shift.trabajador_id.in_(workers)))
            db.execute(delete(Worker).where(Worker.cuenta_id.in_(accounts)))
            db.execute(delete(Account).where(Account.nombre_usuario == username))
            db.execute(delete(Site).where(Site.nombre.in_([site_name, renamed])))


def test_deactivation_waits_for_concurrent_entry(app, sample, monkeypatch):
    entering, release = Event(), Event()

    def clock():
        entering.set()
        assert release.wait(10)
        return datetime.now(UTC)

    monkeypatch.setattr(attendance, "utc_now", clock)
    worker = app.test_client()
    token = login(worker, sample.username)
    admin = app.test_client()
    headers = {"X-CSRF-Token": login(admin, sample.admin_username)}
    path = f"/api/admin/trabajadores/{sample.worker_id}/desactivar"
    with ThreadPoolExecutor(max_workers=2) as pool:
        entry = pool.submit(mark, worker, token, "entrada")
        try:
            assert entering.wait(10)
            deactivation = pool.submit(admin.post, path, headers=headers)
            deadline = monotonic() + 5
            sessions = app.extensions["database_sessions"]
            while not deactivation.done() and monotonic() < deadline:
                with sessions() as db:
                    waiting_for_worker = db.scalar(
                        text(
                            "SELECT EXISTS (SELECT 1 FROM pg_stat_activity "
                            "WHERE datname = current_database() "
                            "AND wait_event_type = 'Lock' "
                            "AND query LIKE '%FROM trabajadores%FOR UPDATE%')"
                        )
                    )
                if waiting_for_worker:
                    break
                sleep(0.02)
            else:
                pytest.fail("La desactivación debe esperar el bloqueo de la marcación.")
        finally:
            release.set()

    assert entry.result().status_code == 200
    assert deactivation.result().status_code == 409
    assert worker.get("/api/asistencia").json["activo"] is True


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
