"""crear tablas de asistencia

Revision ID: 20261112_0001
Revises:
Create Date: 2026-11-12 01:07:11.509565
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20261112_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "cuentas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre_usuario", sa.String(length=80), nullable=False),
        sa.Column("hash_contrasena", sa.Text(), nullable=False),
        sa.Column("rol", sa.String(length=20), nullable=False),
        sa.CheckConstraint(
            "rol IN ('trabajador', 'administrador')", name=op.f("ck_cuentas_rol_valido")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_cuentas")),
        sa.UniqueConstraint("nombre_usuario", name=op.f("uq_cuentas_nombre_usuario")),
    )
    op.create_table(
        "sedes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sedes")),
        sa.UniqueConstraint("nombre", name=op.f("uq_sedes_nombre")),
    )
    op.create_table(
        "trabajadores",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("cuenta_id", sa.Uuid(), nullable=True),
        sa.Column("sede_id", sa.Uuid(), nullable=False),
        sa.Column("nombre", sa.String(length=120), nullable=False),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(
            ["cuenta_id"],
            ["cuentas.id"],
            name=op.f("fk_trabajadores_cuenta_id_cuentas"),
        ),
        sa.ForeignKeyConstraint(
            ["sede_id"], ["sedes.id"], name=op.f("fk_trabajadores_sede_id_sedes")
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_trabajadores")),
        sa.UniqueConstraint("cuenta_id", name=op.f("uq_trabajadores_cuenta_id")),
    )
    op.create_table(
        "jornadas",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("trabajador_id", sa.Uuid(), nullable=False),
        sa.Column("sede_id", sa.Uuid(), nullable=False),
        sa.Column("entrada", sa.DateTime(timezone=True), nullable=False),
        sa.Column("salida", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "salida IS NULL OR salida >= entrada",
            name=op.f("ck_jornadas_tiempo_ordenado"),
        ),
        sa.ForeignKeyConstraint(
            ["sede_id"], ["sedes.id"], name=op.f("fk_jornadas_sede_id_sedes")
        ),
        sa.ForeignKeyConstraint(
            ["trabajador_id"],
            ["trabajadores.id"],
            name=op.f("fk_jornadas_trabajador_id_trabajadores"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_jornadas")),
    )
    op.create_index(
        "ix_jornadas_trabajador_entrada",
        "jornadas",
        ["trabajador_id", "entrada"],
        unique=False,
    )
    op.create_index(
        "uq_jornadas_trabajador_abierta",
        "jornadas",
        ["trabajador_id"],
        unique=True,
        postgresql_where=sa.text("salida IS NULL"),
    )
    op.create_table(
        "solicitudes_marcacion",
        sa.Column("cuenta_id", sa.Uuid(), nullable=False),
        sa.Column("clave_reintento", sa.Uuid(), nullable=False),
        sa.Column("jornada_id", sa.Uuid(), nullable=True),
        sa.Column("operacion", sa.String(length=10), nullable=False),
        sa.Column("estado_http", sa.SmallInteger(), nullable=False),
        sa.Column("resultado", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.CheckConstraint(
            "operacion IN ('entrada', 'salida')",
            name=op.f("ck_solicitudes_marcacion_operacion_valida"),
        ),
        sa.ForeignKeyConstraint(
            ["cuenta_id"],
            ["cuentas.id"],
            name=op.f("fk_solicitudes_marcacion_cuenta_id_cuentas"),
        ),
        sa.ForeignKeyConstraint(
            ["jornada_id"],
            ["jornadas.id"],
            name=op.f("fk_solicitudes_marcacion_jornada_id_jornadas"),
        ),
        sa.PrimaryKeyConstraint(
            "cuenta_id", "clave_reintento", name=op.f("pk_solicitudes_marcacion")
        ),
    )


def downgrade() -> None:
    op.drop_table("solicitudes_marcacion")
    op.drop_index(
        "uq_jornadas_trabajador_abierta",
        table_name="jornadas",
        postgresql_where=sa.text("salida IS NULL"),
    )
    op.drop_index("ix_jornadas_trabajador_entrada", table_name="jornadas")
    op.drop_table("jornadas")
    op.drop_table("trabajadores")
    op.drop_table("sedes")
    op.drop_table("cuentas")
