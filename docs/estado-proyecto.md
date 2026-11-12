# Estado del proyecto

Última actualización: 2026-11-12.

## Objetivo

La primera versión permitirá gestionar trabajadores y sedes, registrar entradas y salidas desde el celular y consultar el historial por trabajador, fecha y sede.

El [alcance del MVP](alcance-mvp.md) recoge las reglas iniciales y las funciones que se pueden incorporar según la operación de cada empresa.

## Qué tenemos hoy

| Área | Estado verificado |
| --- | --- |
| Repositorio | [SISTEMA_ASISTENCIA](https://github.com/steveespinoza/SISTEMA_ASISTENCIA) usa `main` como rama principal. El [README](../README.md) presenta el objetivo, el alcance y la arquitectura propuesta. |
| Producto y arquitectura | Alcance definido. La dirección acordada es un monolito modular con React y TypeScript, Flask y PostgreSQL con SQLAlchemy y Alembic. |
| Guías de desarrollo | [AGENTS.md](../AGENTS.md) reúne las guías de requisitos, implementación, diseño frontend, verificación y revisión de PR. |
| GitHub | [Plantilla de PR](../.github/pull_request_template.md) y [CI](../.github/workflows/ci.yml) para backend y frontend. La plantilla de issues sigue propuesta. |
| Aplicación | Frontend en React, API Flask con `GET /api/health`, PostgreSQL de desarrollo y Alembic configurado. El [arranque local](../README.md#desarrollo-local) incluye una pantalla que comprueba la conexión. |

## Siguiente paso

El siguiente hito es el primer flujo de asistencia con datos ficticios. Crear la primera migración de negocio y conectar inicio de sesión, entrada, salida y consulta de la jornada. El hito se completa cuando ese recorrido se puede ejecutar desde una instalación nueva y comprobar con pruebas.

Después, completar la gestión administrativa y los filtros del historial, y preparar la demo pública. El entorno de despliegue se definirá cuando el flujo funcione en local.
