import click
from flask.cli import with_appcontext
from sqlalchemy import select
from werkzeug.security import generate_password_hash

from asistencia.http import database_sessions
from asistencia.models import Account, Site, Worker

DEMO_USERNAME = "demo.trabajador"


@click.command("cargar-demo")
@with_appcontext
def load_demo() -> None:
    """Crea una cuenta ficticia y un trabajador en una sede de demostración."""
    with database_sessions().begin() as db:
        account = db.scalar(
            select(Account).where(Account.nombre_usuario == DEMO_USERNAME)
        )
        if account is not None:
            click.echo(f"La cuenta {DEMO_USERNAME} ya existe.")
            return

        password = click.prompt(
            "Contraseña para la cuenta ficticia",
            hide_input=True,
            confirmation_prompt=True,
        )
        if not 8 <= len(password) <= 256:
            raise click.ClickException("Usa entre 8 y 256 caracteres.")

        site = db.scalar(select(Site).where(Site.nombre == "Sede de demostración"))
        if site is None:
            site = Site(nombre="Sede de demostración")
            db.add(site)
        account = Account(
            nombre_usuario=DEMO_USERNAME,
            hash_contrasena=generate_password_hash(password),
            rol="trabajador",
        )
        db.add(account)
        db.flush()
        db.add(
            Worker(
                cuenta_id=account.id,
                sede_id=site.id,
                nombre="Trabajador de demostración",
            )
        )

    click.echo(f"Cuenta ficticia creada. Usuario: {DEMO_USERNAME}.")
