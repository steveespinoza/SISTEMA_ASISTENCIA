# Casos de uso

El primer hito cubre CU-01 a CU-04 y se comprueba desde una base vacía según RQ-03. Los casos CU-05 a CU-07 completan el uso administrativo. Los códigos RF, RN y RQ corresponden a los [requisitos del MVP](requisitos.md).

## CU-01 Iniciar sesión

**Actor** · Trabajador o administrador. **Requisito** · RF-01.

1. El usuario introduce su nombre de usuario y contraseña.
2. La API valida las credenciales y establece la sesión con el rol correspondiente.
3. El sistema muestra las opciones disponibles para ese rol.

Con credenciales inválidas, el sistema informa el error y mantiene el formulario. Las operaciones protegidas requieren una sesión válida.

## CU-02 Registrar entrada

**Actor** · Trabajador. **Requisitos** · RF-02, RN-01, RN-02, RN-04, RN-05, RN-06 y RQ-02.

1. El trabajador con sesión válida y sede asignada selecciona **Registrar entrada**.
2. La API comprueba que puede marcar, toma la hora del servidor y abre la jornada con la sede asignada.
3. La pantalla confirma la entrada e indica la sede y la hora registrada.

Si ya hay una jornada abierta, una nueva entrada se rechaza. Si la respuesta se pierde, el trabajador puede reintentar la misma solicitud y recuperar su confirmación.

## CU-03 Registrar salida

**Actor** · Trabajador. **Requisitos** · RF-03, RN-03, RN-04, RN-05, RN-06 y RQ-02.

1. El trabajador con sesión válida y jornada abierta selecciona **Registrar salida**.
2. La API comprueba que la jornada indicada sigue abierta y la cierra con la hora del servidor.
3. La pantalla confirma la salida y el historial muestra la jornada cerrada.

Si la jornada indicada ya se cerró, la pantalla muestra el motivo del rechazo y actualiza la asistencia. El cambio de fecha local no impide cerrar la jornada. El reintento de la misma salida recupera la confirmación original.

## CU-04 Consultar historial propio

**Actor** · Trabajador. **Requisitos** · RF-04, RN-04 y RQ-01.

1. El trabajador inicia sesión y abre **Mi asistencia**.
2. La API obtiene las jornadas del trabajador vinculado a la cuenta.
3. El historial muestra sede, entrada, salida y estado. Para una jornada cerrada, también muestra el tiempo transcurrido.

El sistema muestra un estado vacío si todavía no hay jornadas. Una solicitud de historial de otro trabajador se deniega.

## CU-05 Gestionar sedes y asignaciones

**Actor** · Administrador. **Requisitos** · RF-05, RN-01 y RQ-01.

1. El administrador registra o actualiza los datos de una sede.
2. Selecciona un trabajador y le asigna una sede.
3. La nueva asignación se utiliza en la próxima entrada. Las jornadas anteriores conservan la sede registrada.

## CU-06 Gestionar trabajadores

**Actor** · Administrador. **Requisitos** · RF-06, RN-06 y RQ-01.

1. El administrador registra o actualiza los datos de un trabajador.
2. Cuando el administrador solicita la desactivación, la API comprueba si el trabajador tiene una jornada abierta.
3. El sistema desactiva al trabajador, bloquea nuevas marcaciones y mantiene su historial disponible para el administrador.

Si hay una jornada abierta, la API rechaza la desactivación y mantiene al trabajador activo. El trabajador debe marcar su salida antes de que el administrador vuelva a solicitarla.

## CU-07 Consultar asistencia del personal

**Actor** · Administrador. **Requisitos** · RF-07, RN-07 y RQ-01.

1. El administrador abre el historial y elige un período. Puede filtrar por trabajador y sede.
2. La API devuelve las jornadas cuya fecha de entrada cae en el período, en la zona horaria de la empresa, y que coinciden con los demás filtros.
3. La vista muestra los filtros activos y distingue las jornadas abiertas de las cerradas. Si el filtro no devuelve registros, indica que no hubo coincidencias.
