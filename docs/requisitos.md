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
| RF-07 | Permitir que el administrador consulte jornadas abiertas, cerradas y sin salida por trabajador, sede y fecha de entrada. | Administración |

## Reglas de negocio

| ID | Regla | Cómo comprobarla |
| --- | --- | --- |
| RN-01 | La entrada abre una jornada y toma la sede asignada al trabajador en ese momento. | La jornada conserva esa sede si la asignación del trabajador cambia después. |
| RN-02 | Cada trabajador puede registrar una asistencia por día calendario en la zona horaria de la empresa. | Dos entradas simultáneas dejan una sola jornada. Otra entrada el mismo día se rechaza aunque la jornada ya esté cerrada. |
| RN-03 | La salida solo cierra la jornada indicada si sigue abierta y pertenece al día actual. | Si falta la salida al cambiar el día, la jornada figura como **Sin salida** con hora de salida y duración vacías. La entrada del día siguiente abre una nueva jornada. Una salida desde una pantalla desactualizada se rechaza. |
| RN-04 | La hora de marcación viene del servidor. Los instantes se guardan en UTC y se muestran en la zona horaria de la empresa. | Una hora incorrecta en el celular deja intacto el instante registrado por la API. |
| RN-05 | Un reintento de la misma marcación con el mismo identificador devuelve el resultado original. | Si se pierde la respuesta de una entrada exitosa, el reintento confirma la misma jornada y la misma hora. Aplica también a la salida. |
| RN-06 | Una jornada abierta del día impide desactivar al trabajador. Una vez desactivado, conserva su historial y queda inhabilitado para nuevas marcaciones. | La API rechaza la desactivación si hay una jornada pendiente del día. La permite tras registrar la salida o al cambiar el día. Las marcaciones nuevas se rechazan incluso con una sesión previa. |
| RN-07 | El filtro por período usa la fecha de entrada en la zona horaria de la empresa. | Una jornada del lunes que queda **Sin salida** aparece al filtrar por lunes. |

## Requisitos de calidad

| ID | Requisito | Cómo comprobarlo |
| --- | --- | --- |
| RQ-01 | La API limita al trabajador a sus propias marcaciones e historial. La consulta global y la gestión de personal y sedes son administrativas. | Un trabajador recibe una denegación al consultar el historial ajeno o usar una operación administrativa. |
| RQ-02 | El flujo de marcación se puede completar desde el celular. La interfaz distingue carga, confirmación y resultado sin confirmar. | Completar entrada y salida en una pantalla estrecha. Simular una respuesta perdida y verificar que se pueda reintentar la misma solicitud. |
| RQ-03 | El primer flujo se puede reproducir desde una base PostgreSQL vacía. | Aplicar las migraciones, cargar datos ficticios y completar inicio de sesión, entrada, salida y consulta del historial. |

## Sesión y cuenta de demostración

La sesión web tiene una vigencia de ocho horas. La demo usa una cuenta ficticia creada con un comando local. En una instalación nueva, el operador crea la primera cuenta administrativa con `crear-administrador`. El administrador registra a los trabajadores con usuario, contraseña inicial y sede. [Decisión sobre la sesión web](decisiones/0001-sesion-web.md)
