# Alcance del MVP

La base permite que una empresa registre quién trabajó, cuándo marcó y en qué sede. La instalación inicial atiende a una empresa con varias sedes y una base PostgreSQL propia.

## Funciones incluidas

- **Acceso.** El administrador y el trabajador inician sesión con nombre de usuario y contraseña.
- **Administrador.** Gestiona trabajadores y sedes. Consulta jornadas abiertas, cerradas y sin salida con filtros por trabajador, sede y fecha de entrada.
- **Trabajador.** Registra su propia entrada y salida desde una cuenta y consulta su historial.
- **Jornada.** La entrada registra al trabajador, la sede asignada y la hora del servidor. Se admite una asistencia por trabajador y día calendario en la zona horaria de la empresa. La salida se registra el mismo día. Al cambiar el día, una jornada pendiente figura como **Sin salida** y se puede registrar la nueva entrada.
- **Historial.** Una nueva asignación de sede conserva las jornadas anteriores. El administrador puede desactivar a un trabajador cuando no tiene una jornada abierta del día. La desactivación conserva el historial e impide nuevas marcaciones.
- **Tiempo.** Los instantes se almacenan en UTC y se muestran en la zona horaria de la empresa. El historial presenta el tiempo transcurrido de la jornada cerrada.
- **Reintentos.** Repetir la misma solicitud de marcación devuelve el resultado original. Las solicitudes simultáneas respetan el límite de una asistencia por día.

## Extensiones por solicitud

Kiosco, rol delegado, geocerca, fotos y almacenamiento de evidencia, correcciones manuales de marcación, horarios y reglas de planilla, préstamos entre sedes, historial de asignaciones con vigencia, formatos de exportación y catálogos particulares.

Si se incorpora una política de jornada o planilla, define su vigencia y cómo reproducir el cálculo de un período pasado. El tiempo transcurrido del MVP es un registro de asistencia. El cálculo de horas pagables pertenece a la extensión de planilla.

## Dirección técnica

Monolito modular con React y TypeScript en la interfaz, Flask en la API y SQLAlchemy y Alembic para PostgreSQL. Los módulos previstos son identidad y permisos, personal y sedes, asistencia y consultas. El primer flujo completo será inicio de sesión, entrada, salida y consulta, con una empresa ficticia para la demo.
