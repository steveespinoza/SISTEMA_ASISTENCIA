import click
from flask.cli import with_appcontext
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from werkzeug.security import generate_password_hash

from asistencia.http import database_sessions
from asistencia.models import Account

USERNAME_LIMIT = 80
MIN_NEW_PASSWORD_LENGTH = 8
PASSWORD_LIMIT = 256
PASSWORD_LENGTH_MESSAGE = (
    f"Usa entre {MIN_NEW_PASSWORD_LENGTH} y {PASSWORD_LIMIT} caracteres de contraseña."
)


def create_account(
    db: Session, username: str, password_hash: str, role: str
) -> Account | None:
    return db.scalar(
        insert(Account)
        .values(nombre_usuario=username, hash_contrasena=password_hash, rol=role)
        .on_conflict_do_nothing(index_elements=[Account.nombre_usuario])
        .returning(Account)
    )


@click.command("crear-administrador")
@click.option("--usuario", prompt="Usuario del administrador")
@with_appcontext
def create_first_admin(usuario: str) -> None:
    """Crea la primera cuenta administrativa de esta instalación."""
    username = usuario.strip()
    if not 1 <= len(username) <= USERNAME_LIMIT or "\0" in username:
        raise click.ClickException(
            f"Usa entre 1 y {USERNAME_LIMIT} caracteres de usuario."
        )
    password = click.prompt(
        "Contraseña del administrador", hide_input=True, confirmation_prompt=True
    )
    if not MIN_NEW_PASSWORD_LENGTH <= len(password) <= PASSWORD_LIMIT:
        raise click.ClickException(PASSWORD_LENGTH_MESSAGE)
    password_hash = generate_password_hash(password)

    with database_sessions().begin() as db:
        # Serializa la inicialización si se ejecuta el comando en dos terminales.
        db.execute(
            select(
                func.pg_advisory_xact_lock(
                    func.hashtext("asistencia.crear-administrador")
                )
            )
        )
        if db.scalar(select(Account.id).where(Account.rol == "administrador").limit(1)):
            raise click.ClickException("Ya existe una cuenta administrativa.")
        if create_account(db, username, password_hash, "administrador") is None:
            raise click.ClickException("El nombre de usuario ya está en uso.")

    click.echo(f"Cuenta administrativa creada. Usuario: {username}.")
