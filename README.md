# Sistema de Asistencia

Este proyecto nace de un sistema de asistencia que desarrollé para una empresa con varias sedes. Quiero que cada trabajador pueda marcar su entrada y salida desde el celular y que el administrador pueda revisar quién marcó, a qué hora y en qué sede.

El proyecto está en etapa de diseño del MVP.

## Qué cubrirá el MVP

| Rol | Funciones |
| --- | --- |
| Trabajador | Registrar su propia entrada y salida, ver la confirmación de la marcación y consultar su historial. |
| Administrador | Gestionar trabajadores y sedes, y consultar jornadas abiertas y cerradas con filtros. |

Cada trabajador podrá tener una sola jornada abierta. Si falla la conexión y vuelve a enviar la marcación, se conservará un único registro. El historial mantendrá la sede donde se registró cada jornada.

La primera versión cubrirá la marcación y el historial. Funciones como geocercas, fotos o reglas de planilla se incorporarán según cómo trabaje cada empresa.

## Arquitectura propuesta

Elegí **React con TypeScript** para la interfaz y **Flask** para la API. La API será un monolito modular para desplegar un solo servicio y mantener claras las responsabilidades de identidad, personal, asistencia y consultas. Usaré **PostgreSQL** con **SQLAlchemy** y **Alembic** para el acceso a datos y las migraciones.

El primer flujo conectará inicio de sesión, entrada, salida y consulta del historial. Su verificación incluirá una instalación desde una base vacía y pruebas de las reglas de marcación en PostgreSQL.

## Documentación

- [Alcance del MVP](docs/alcance-mvp.md)
- [Estado y siguiente hito](docs/estado-proyecto.md)
- [Guías de trabajo y revisión](AGENTS.md)
