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
| Diseño del MVP | [Requisitos](requisitos.md), [casos de uso](casos-de-uso.md) y [diagramas](arquitectura.md) preparados. Acceso con usuario y contraseña, filtro por fecha de entrada y bloqueo de la desactivación con una jornada abierta. |
| GitHub | [Plantilla de PR](../.github/pull_request_template.md) y [CI](../.github/workflows/ci.yml) para backend y frontend. La plantilla de issues sigue propuesta. |
| Aplicación | El [flujo local](../README.md#desarrollo-local) permite iniciar sesión, marcar entrada y salida y consultar el historial propio. La [salida](casos-de-uso.md#cu-03-registrar-salida) comprueba que la jornada mostrada sigue abierta. Alembic crea el esquema y el comando de demo carga una cuenta ficticia. |
| Administración | El [alta inicial](../README.md#gestión-administrativa) habilita la primera cuenta administrativa. Su vista permite crear y editar sedes, registrar y reasignar trabajadores y desactivarlos cuando su jornada esté cerrada. |
| Historial administrativo | El administrador puede [consultar jornadas](casos-de-uso.md#cu-07-consultar-asistencia-del-personal) abiertas y cerradas por fecha de entrada, trabajador y sede registrada. El período usa la zona horaria de la empresa. |
| Base de desarrollo | Flask y Vite se ejecutan en local y pueden usar PostgreSQL en Neon. El [README](../README.md#configurar-la-base-de-datos) explica cómo configurar la conexión directa. |
| Asistencia diaria | Se admite una asistencia por día en la zona horaria de la empresa. Las jornadas vencidas quedan como **Sin salida** y permiten marcar una nueva entrada. |

## Siguiente paso

El alcance funcional del MVP está implementado y se ejecuta en local. El despliegue público queda pospuesto.
