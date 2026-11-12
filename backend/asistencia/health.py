from flask import Blueprint, Response, current_app, jsonify
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

health_api = Blueprint("health", __name__, url_prefix="/api")


@health_api.get("/health")
def health() -> Response:
    engine = current_app.extensions["database_engine"]

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError:
        current_app.logger.warning("La comprobación de conexión a PostgreSQL falló.")
        response = jsonify(database="unavailable")
        response.status_code = 503
    else:
        response = jsonify(database="available")

    return response
