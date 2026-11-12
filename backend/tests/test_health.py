import os

import pytest

from asistencia import create_app

TEST_SECRET = "clave-ficticia-exclusiva-de-las-pruebas"


def test_health_responds_when_postgresql_is_available():
    database_url = os.getenv("TEST_DATABASE_URL")
    if not database_url:
        pytest.skip("Define TEST_DATABASE_URL con una base PostgreSQL descartable.")

    app = create_app(database_url, secret_key=TEST_SECRET)
    try:
        response = app.test_client().get("/api/health")

        assert response.status_code == 200
        assert response.get_json() == {"database": "available"}
        assert response.headers["Cache-Control"] == "no-store"
    finally:
        app.extensions["database_engine"].dispose()


def test_health_returns_service_unavailable_when_postgresql_cannot_be_reached():
    app = create_app(
        "postgresql+psycopg://test:test@127.0.0.1:1/test", secret_key=TEST_SECRET
    )
    try:
        response = app.test_client().get("/api/health")

        assert response.status_code == 503
        assert response.get_json() == {"database": "unavailable"}
        assert response.headers["Cache-Control"] == "no-store"
    finally:
        app.extensions["database_engine"].dispose()
