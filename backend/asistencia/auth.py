from flask import Blueprint, Response, jsonify, request, session
from sqlalchemy import select
from werkzeug.security import check_password_hash, generate_password_hash

from asistencia.accounts import PASSWORD_LIMIT, USERNAME_LIMIT
from asistencia.http import (
    ApiError,
    csrf_token,
    database_sessions,
    require_csrf,
    session_account_id,
)
from asistencia.models import Account

auth_api = Blueprint("auth", __name__, url_prefix="/api/auth")
DUMMY_PASSWORD_HASH = generate_password_hash("cuenta-ficticia-no-utilizable")


def session_payload(account: Account | None) -> Response:
    user = None
    if account is not None:
        user = {"usuario": account.nombre_usuario, "rol": account.rol}
    return jsonify(usuario=user, csrf_token=csrf_token())


@auth_api.get("/sesion")
def current_session() -> Response:
    account_id = session_account_id()
    if account_id is None:
        return session_payload(None)

    with database_sessions()() as db:
        account = db.get(Account, account_id)
        if account is None:
            session.clear()
        return session_payload(account)


@auth_api.post("/iniciar-sesion")
def login() -> Response:
    require_csrf()
    data = request.get_json(silent=True)
    username = data.get("usuario") if isinstance(data, dict) else None
    password = data.get("contrasena") if isinstance(data, dict) else None
    if not isinstance(username, str) or not isinstance(password, str):
        raise ApiError(400, "Ingresa tu usuario y contraseña.")
    username = username.strip()
    if (
        not 1 <= len(username) <= USERNAME_LIMIT
        or not 1 <= len(password) <= PASSWORD_LIMIT
    ):
        raise ApiError(400, "Revisa el usuario y la contraseña ingresados.")

    with database_sessions()() as db:
        account = db.scalar(select(Account).where(Account.nombre_usuario == username))
        password_hash = account.hash_contrasena if account else DUMMY_PASSWORD_HASH
        if not check_password_hash(password_hash, password) or account is None:
            raise ApiError(
                401, "El usuario o la contraseña son incorrectos.", "login_failed"
            )

        session.clear()
        session["cuenta_id"] = str(account.id)
        session.permanent = True
        return session_payload(account)


@auth_api.post("/cerrar-sesion")
def logout() -> Response:
    require_csrf()
    session.clear()
    return session_payload(None)
