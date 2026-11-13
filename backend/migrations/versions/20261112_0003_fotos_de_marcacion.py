"""Guarda las referencias de las fotos de entrada y salida.

Revision ID: 20261112_0003
Revises: 20261112_0002
"""

import sqlalchemy as sa
from alembic import op

revision = "20261112_0003"
down_revision = "20261112_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("jornadas", sa.Column("foto_entrada", sa.Text(), nullable=True))
    op.add_column("jornadas", sa.Column("foto_salida", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("jornadas", "foto_salida")
    op.drop_column("jornadas", "foto_entrada")
