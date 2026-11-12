# Estado del proyecto

Última actualización: 2026-11-12.

## Qué queremos construir

Un sistema de asistencia genérico para presentar en GitHub y ofrecer como base adaptable a distintas empresas. La primera versión permitirá que una empresa con varias sedes gestione trabajadores, registre entradas y salidas y consulte el historial. La demo usará datos ficticios.

El [alcance del MVP](alcance-mvp.md) define las reglas y las extensiones que una empresa puede solicitar. El diseño toma como referencia flujos de asistencia utilizados en empresas. El repositorio y la demo tienen identidad propia.

## Qué tenemos hoy

| Área | Estado verificado |
| --- | --- |
| Repositorio | [SISTEMA_ASISTENCIA](https://github.com/steveespinoza/SISTEMA_ASISTENCIA) usa `main` como rama principal. El [README](../README.md) presenta el objetivo, el alcance y la arquitectura propuesta. |
| Producto y arquitectura | Alcance definido. La dirección acordada es un monolito modular con React y TypeScript, Flask y PostgreSQL con SQLAlchemy y Alembic. |
| Guías para la IA | [AGENTS.md](../AGENTS.md) enlaza cinco skills locales para requisitos, implementación, diseño frontend, verificación y PR. Su formato y sus enlaces se validaron. |
| GitHub | [Plantilla de PR](../.github/pull_request_template.md) preparada. CI y la plantilla de issues están propuestos. |
| Aplicación | Pendiente de iniciar. La carpeta contiene documentación, skills y la plantilla de PR. Aún no hay servicios, esquema, migraciones ni pruebas de la aplicación. |

## Siguiente paso

El primer hito de implementación es un flujo de punta a punta con datos ficticios. Iniciar PostgreSQL desde cero con Alembic y conectar inicio de sesión, entrada, salida y consulta de la jornada. El hito se completa cuando ese recorrido se puede ejecutar desde una instalación nueva y comprobar con pruebas.

Después, completar la gestión administrativa y los filtros del historial, preparar la demo pública y configurar CI. El despliegue del nuevo proyecto se definirá por separado del sistema de referencia.
