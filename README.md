# Sistema de Asistencia

Este proyecto nace de un sistema de asistencia que desarrollé para una empresa con varias sedes. La primera versión permitirá marcar entradas y salidas desde el celular y consultar el historial por trabajador, fecha y sede.

**Estado actual:** diseño del MVP y preparación del repositorio. El primer hito funcional será demostrar el recorrido completo con una empresa ficticia.

## Qué cubrirá el MVP

| Rol | Funciones |
| --- | --- |
| Trabajador | Registrar su propia entrada y salida, ver la confirmación de la marcación y consultar su historial. |
| Administrador | Gestionar trabajadores y sedes, y consultar jornadas abiertas y cerradas con filtros. |

El diseño contempla una sola jornada abierta por trabajador, reintentos sin duplicar marcaciones y conservación de la sede histórica. Funciones como kiosco, geocercas, evidencia fotográfica y reglas de planilla se podrán incorporar según las necesidades de cada empresa.

## Arquitectura propuesta

La interfaz usará **React y TypeScript**. La API usará **Flask** y organizará sus casos de uso en un monolito modular con cuatro áreas: identidad y permisos, personal y sedes, asistencia y consultas. La persistencia usará **PostgreSQL**, **SQLAlchemy** y migraciones con **Alembic**.

El primer flujo conectará inicio de sesión, entrada, salida y consulta del historial. Su verificación incluirá una instalación desde una base vacía y pruebas de las reglas de marcación en PostgreSQL.

## Documentación

- [Alcance del MVP](docs/alcance-mvp.md)
- [Estado y siguiente hito](docs/estado-proyecto.md)
