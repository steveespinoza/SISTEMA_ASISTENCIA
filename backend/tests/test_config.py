from sqlalchemy import make_url

from asistencia.config import get_database_url


def test_neon_connection_url_uses_psycopg_and_preserves_tls_options(monkeypatch):
    monkeypatch.setenv(
        "DATABASE_URL",
        "postgresql://demo:example%40password@demo.neon.tech/asistencia"
        "?sslmode=require&channel_binding=require",
    )

    url = make_url(get_database_url())
    assert url.drivername == "postgresql+psycopg"
    assert url.password == "example@password"
    assert dict(url.query) == {"sslmode": "require", "channel_binding": "require"}
