import os
from datetime import timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from flask import Flask, Response, jsonify
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from asistencia.accounts import create_first_admin
from asistencia.admin import admin_api
from asistencia.attendance import attendance_api
from asistencia.auth import auth_api
from asistencia.config import get_database_url, load_local_env
from asistencia.database import create_database_engine
from asistencia.demo import load_demo
from asistencia.evidence import MAX_PHOTO_BYTES, PhotoStorage, PhotoStorageUnavailable
from asistencia.health import health_api
from asistencia.http import ApiError


def create_app(
    database_url: str | None = None, *, secret_key: str | None = None
) -> Flask:
    load_local_env()
    secret_key = secret_key or os.getenv("FLASK_SECRET_KEY", "").strip()
    if len(secret_key) < 32:
        raise RuntimeError("Define FLASK_SECRET_KEY con al menos 32 caracteres.")
    timezone = os.getenv("COMPANY_TIMEZONE", "America/Lima")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as error:
        raise RuntimeError(
            "COMPANY_TIMEZONE debe ser una zona horaria IANA."
        ) from error

    app = Flask(__name__)
    app.config.update(
        SECRET_KEY=secret_key,
        SESSION_COOKIE_NAME="asistencia_session",
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=os.getenv("SESSION_COOKIE_SECURE", "1") != "0",
        PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
        SESSION_REFRESH_EACH_REQUEST=False,
        COMPANY_TIMEZONE=timezone,
        MAX_CONTENT_LENGTH=16 * 1024,
    )

    engine = create_database_engine(database_url or get_database_url())
    app.extensions["database_engine"] = engine
    app.extensions["database_sessions"] = sessionmaker(bind=engine)
    bucket = os.getenv("AWS_S3_BUCKET", "").strip()
    if bucket:
        app.extensions["photo_storage"] = PhotoStorage(
            bucket, os.getenv("AWS_REGION") or None
        )
        app.config["PHOTO_REQUEST_LIMIT"] = MAX_PHOTO_BYTES + 16 * 1024
    app.register_blueprint(health_api)
    app.register_blueprint(auth_api)
    app.register_blueprint(attendance_api)
    app.register_blueprint(admin_api)
    app.cli.add_command(create_first_admin)
    app.cli.add_command(load_demo)

    @app.errorhandler(ApiError)
    def handle_api_error(error: ApiError) -> tuple[Response, int]:
        return jsonify(error=error.message, codigo=error.code), error.status

    @app.errorhandler(OperationalError)
    def handle_database_error(_error: OperationalError) -> tuple[Response, int]:
        app.logger.warning("PostgreSQL no está disponible.")
        return jsonify(error="El servicio no está disponible en este momento."), 503

    @app.errorhandler(PhotoStorageUnavailable)
    def handle_photo_storage_error(
        error: PhotoStorageUnavailable,
    ) -> tuple[Response, int]:
        app.logger.warning(
            "S3 no está disponible para la evidencia de asistencia.", exc_info=error
        )
        return jsonify(
            error="No se pudo acceder al almacenamiento de fotos. Inténtalo otra vez.",
            codigo="photo_storage_unavailable",
        ), 503

    @app.after_request
    def prevent_caching(response: Response) -> Response:
        response.headers["Cache-Control"] = "no-store"
        return response

    return app
