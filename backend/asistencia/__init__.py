from flask import Flask

from asistencia.config import get_database_url
from asistencia.database import create_database_engine
from asistencia.health import health_api


def create_app(database_url: str | None = None) -> Flask:
    app = Flask(__name__)
    app.extensions["database_engine"] = create_database_engine(
        database_url or get_database_url()
    )
    app.register_blueprint(health_api)
    return app
