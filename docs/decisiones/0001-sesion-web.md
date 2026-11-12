# Sesión web con cookie de Flask

La aplicación web inicia sesión con nombre de usuario y contraseña. En desarrollo, Vite reenvía `/api` a Flask. El navegador consulta la API bajo el mismo origen que la interfaz.

Flask firma una cookie que identifica la cuenta y tiene una vigencia de ocho horas. La cookie usa `HttpOnly` y `SameSite=Lax`. Se envía con `Secure` por defecto y el entorno local usa HTTP mediante la configuración de ejemplo. La API comprueba un token contra CSRF en las operaciones que cambian estado y renueva el token al iniciar o cerrar sesión.

La API consulta el rol y la asignación del trabajador en PostgreSQL. Las contraseñas se almacenan como hashes scrypt. El cierre de sesión borra la sesión del navegador. El despliegue deberá conservar el mismo origen para la web y `/api` mediante un proxy o una configuración equivalente.
