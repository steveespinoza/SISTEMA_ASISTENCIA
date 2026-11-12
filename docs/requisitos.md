# Requisitos del MVP

El sistema registra la asistencia de una empresa con varias sedes. El [alcance del MVP](alcance-mvp.md) delimita el producto. Los identificadores de esta página enlazan los requisitos con los [casos de uso](casos-de-uso.md) y sus criterios de aceptación.

## Requisitos funcionales

| ID | Requisito | Hito |
| --- | --- | --- |
| RF-01 | Permitir el inicio de sesión con nombre de usuario y contraseña, y aplicar los permisos del rol en la API. | Marcación |
| RF-02 | Permitir que un trabajador activo y asignado a una sede registre su propia entrada. | Marcación |
| RF-03 | Permitir que un trabajador activo cierre su jornada abierta mediante una salida. | Marcación |
| RF-04 | Mostrar al trabajador su historial con sede, entrada, salida, estado y duración de las jornadas cerradas. | Marcación |
| RF-05 | Permitir que el administrador gestione sedes y asigne una sede a cada trabajador. | Administración |
| RF-06 | Permitir que el administrador gestione y desactive trabajadores conservando sus jornadas. | Administración |
| RF-07 | Permitir que el administrador consulte jornadas abiertas y cerradas por trabajador, sede y fecha de entrada. | Administración |

## Reglas de negocio

| ID | Regla | Cómo comprobarla |
| --- | --- | --- |
| RN-01 | La entrada abre una jornada y toma la sede asignada al trabajador en ese momento. | La jornada conserva esa sede si la asignación del trabajador cambia después. |
| RN-02 | Cada trabajador puede tener una sola jornada abierta. | Dos entradas simultáneas con identificadores distintos dejan una sola jornada abierta. La otra petición recibe un conflicto. |
| RN-03 | La salida identifica la jornada que el trabajador está viendo y solo la cierra si sigue abierta, aunque la fecha local haya cambiado. | Una entrada a las 22:00 y una salida a las 06:00 del día siguiente forman una jornada cerrada de 8 horas. Si otra sesión ya cerró esa jornada y abrió una nueva, la salida de la pantalla anterior se rechaza y la jornada nueva sigue abierta. |
| RN-04 | La hora de marcación viene del servidor. Los instantes se guardan en UTC y se muestran en la zona horaria de la empresa. | Una hora incorrecta en el celular deja intacto el instante registrado por la API. |
| RN-05 | Un reintento de la misma marcación con el mismo identificador devuelve el resultado original. | Si se pierde la respuesta de una entrada exitosa, el reintento confirma la misma jornada y la misma hora. Aplica también a la salida. |
| RN-06 | Un trabajador solo se puede desactivar cuando no tiene una jornada abierta. Una vez desactivado, conserva su historial y queda inhabilitado para nuevas marcaciones. | Con una jornada abierta, la API rechaza la desactivación y el trabajador sigue activo. Después de que marque la salida, el administrador puede desactivarlo. El historial se conserva y la API rechaza nuevas marcaciones, incluso si el trabajador ya tenía una sesión. |
| RN-07 | El filtro por período usa la fecha de entrada en la zona horaria de la empresa. | Una jornada que empieza el lunes a las 22:00 y termina el martes a las 06:00 aparece al filtrar por lunes. |

## Requisitos de calidad

| ID | Requisito | Cómo comprobarlo |
| --- | --- | --- |
| RQ-01 | La API limita al trabajador a sus propias marcaciones e historial. La consulta global y la gestión de personal y sedes son administrativas. | Un trabajador recibe una denegación al consultar el historial ajeno o usar una operación administrativa. |
| RQ-02 | El flujo de marcación se puede completar desde el celular. La interfaz distingue carga, confirmación y resultado sin confirmar. | Completar entrada y salida en una pantalla estrecha. Simular una respuesta perdida y verificar que se pueda reintentar la misma solicitud. |
| RQ-03 | El primer flujo se puede reproducir desde una base PostgreSQL vacía. | Aplicar las migraciones, cargar datos ficticios y completar inicio de sesión, entrada, salida y consulta del historial. |

## Sesión y cuenta de demostración

La sesión web tiene una vigencia de ocho horas. La demo usa una cuenta ficticia creada con un comando local. En una instalación nueva, el operador crea la primera cuenta administrativa con `crear-administrador`. El administrador registra a los trabajadores con usuario, contraseña inicial y sede. [Decisión sobre la sesión web](decisiones/0001-sesion-web.md)
