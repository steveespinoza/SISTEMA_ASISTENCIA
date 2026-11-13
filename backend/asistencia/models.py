from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    SmallInteger,
    String,
    Text,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from asistencia.database import Base


class Account(Base):
    __tablename__ = "cuentas"
    __table_args__ = (
        CheckConstraint("rol IN ('trabajador', 'administrador')", name="rol_valido"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nombre_usuario: Mapped[str] = mapped_column(String(80), unique=True)
    hash_contrasena: Mapped[str] = mapped_column(Text)
    rol: Mapped[str] = mapped_column(String(20))


class Site(Base):
    __tablename__ = "sedes"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nombre: Mapped[str] = mapped_column(String(120), unique=True)


class Worker(Base):
    __tablename__ = "trabajadores"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    cuenta_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("cuentas.id"), unique=True
    )
    sede_id: Mapped[UUID] = mapped_column(ForeignKey("sedes.id"))
    nombre: Mapped[str] = mapped_column(String(120))
    activo: Mapped[bool] = mapped_column(default=True)


class Shift(Base):
    __tablename__ = "jornadas"
    __table_args__ = (
        CheckConstraint("salida IS NULL OR salida >= entrada", name="tiempo_ordenado"),
        CheckConstraint(
            "NOT sin_salida OR salida IS NULL", name="sin_salida_coherente"
        ),
        Index(
            "uq_jornadas_trabajador_abierta",
            "trabajador_id",
            unique=True,
            postgresql_where=text("salida IS NULL AND NOT sin_salida"),
        ),
        Index("ix_jornadas_trabajador_entrada", "trabajador_id", "entrada"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    trabajador_id: Mapped[UUID] = mapped_column(ForeignKey("trabajadores.id"))
    sede_id: Mapped[UUID] = mapped_column(ForeignKey("sedes.id"))
    entrada: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    salida: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    sin_salida: Mapped[bool] = mapped_column(server_default=text("false"))


class MarkRequest(Base):
    __tablename__ = "solicitudes_marcacion"
    __table_args__ = (
        CheckConstraint("operacion IN ('entrada', 'salida')", name="operacion_valida"),
    )

    cuenta_id: Mapped[UUID] = mapped_column(ForeignKey("cuentas.id"), primary_key=True)
    clave_reintento: Mapped[UUID] = mapped_column(primary_key=True)
    jornada_id: Mapped[UUID | None] = mapped_column(ForeignKey("jornadas.id"))
    operacion: Mapped[str] = mapped_column(String(10))
    estado_http: Mapped[int] = mapped_column(SmallInteger)
    resultado: Mapped[dict] = mapped_column(JSONB)
