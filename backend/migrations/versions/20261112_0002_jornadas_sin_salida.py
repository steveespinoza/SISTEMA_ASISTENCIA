"""Distingue las jornadas vencidas de las abiertas.

Revision ID: 20261112_0002
Revises: 20261112_0001
"""

import sqlalchemy as sa
from alembic import op

revision = "20261112_0002"
down_revision = "20261112_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "jornadas",
        sa.Column(
            "sin_salida", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
    )
    op.create_check_constraint(
        op.f("ck_jornadas_sin_salida_coherente"),
        "jornadas",
        "NOT sin_salida OR salida IS NULL",
    )
    op.drop_index("uq_jornadas_trabajador_abierta", table_name="jornadas")
    op.create_index(
        "uq_jornadas_trabajador_abierta",
        "jornadas",
        ["trabajador_id"],
        unique=True,
        postgresql_where=sa.text("salida IS NULL AND NOT sin_salida"),
    )


def downgrade() -> None:
    # El índice anterior impide volver a un esquema que no representa estos datos.
    op.drop_index("uq_jornadas_trabajador_abierta", table_name="jornadas")
    op.create_index(
        "uq_jornadas_trabajador_abierta",
        "jornadas",
        ["trabajador_id"],
        unique=True,
        postgresql_where=sa.text("salida IS NULL"),
    )
    op.drop_constraint(
        op.f("ck_jornadas_sin_salida_coherente"), "jornadas", type_="check"
    )
    op.drop_column("jornadas", "sin_salida")
