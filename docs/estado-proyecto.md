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
| GitHub | [Plantilla de PR](../.github/pull_request_template.md) preparada. CI y la plantilla de issues están propuestos. |
| Aplicación | Pendiente de iniciar. La carpeta contiene documentación y la plantilla de PR. Aún no hay servicios, esquema, migraciones ni pruebas de la aplicación. |

## Siguiente paso

El primer hito de implementación es un flujo de punta a punta con datos ficticios. Iniciar PostgreSQL desde cero con Alembic y conectar inicio de sesión, entrada, salida y consulta de la jornada. El hito se completa cuando ese recorrido se puede ejecutar desde una instalación nueva y comprobar con pruebas.

Después, completar la gestión administrativa y los filtros del historial, preparar la demo pública y configurar CI. El entorno de despliegue se definirá cuando el flujo funcione en local.
