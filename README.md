# Sistema de Asistencia

Este proyecto nace de un sistema de asistencia que desarrollé para una empresa con varias sedes. Quiero que cada trabajador pueda marcar su entrada y salida desde el celular y que el administrador pueda revisar quién marcó, a qué hora y en qué sede.

En local, el trabajador puede iniciar sesión, marcar su entrada y salida y consultar su historial. El administrador puede gestionar sedes y trabajadores y consultar las jornadas del personal.

## Alcance del MVP

| Rol | Funciones |
| --- | --- |
| Trabajador | Registrar su propia entrada y salida, ver la confirmación de la marcación y consultar su historial. |
| Administrador | Gestionar trabajadores y sedes, y consultar jornadas abiertas y cerradas con filtros. |

Cada trabajador podrá tener una sola jornada abierta. Si falla la conexión y vuelve a enviar la marcación, se conservará un único registro. El historial mantendrá la sede donde se registró cada jornada.

La primera versión cubrirá la marcación y el historial. Funciones como geocercas, fotos o reglas de planilla se incorporarán según cómo trabaje cada empresa.

## Arquitectura propuesta

Elegí **React con TypeScript** para la interfaz y **Flask** para la API. La API será un monolito modular para desplegar un solo servicio y mantener claras las responsabilidades de identidad, personal, asistencia y consultas. Usaré **PostgreSQL** con **SQLAlchemy** y **Alembic** para el acceso a datos y las migraciones.

Las reglas de marcación se comprueban con pruebas sobre PostgreSQL, incluidas entradas simultáneas, reintentos y jornadas que cruzan medianoche.

## Desarrollo local

Necesitas Python 3.13, uv, Node.js 24 con npm y una base PostgreSQL. Flask y Vite se ejecutan en tu equipo.

### Configurar la base de datos

Desde la raíz del repositorio, copia `.env.example` a `.env` si aún no existe. En PowerShell puedes usar `Copy-Item .env.example .env`. Configura `DATABASE_URL` según la base que uses.

- **Neon.** En **Connect**, selecciona la base de desarrollo y desactiva **Connection pooling** para copiar su URL directa. Pega la URL completa en `DATABASE_URL`. El backend acepta el prefijo `postgresql://` de Neon y conserva los parámetros de conexión, incluido `sslmode=require`. Git excluye `.env`, que contiene la contraseña de la base. [Conexión a Neon](https://neon.com/docs/connect/connect-from-any-app)
- **PostgreSQL en tu equipo.** Puedes apuntar `DATABASE_URL` a una base de desarrollo existente. Si prefieres Docker, deja la URL de ejemplo y ejecuta este comando desde la raíz. Compose inicia PostgreSQL 17 en el puerto local 5432.

```sh
docker compose up -d --wait db
```

### Iniciar Flask y Vite

En una terminal, instala las dependencias del backend. Si `FLASK_SECRET_KEY` está vacía, genera una clave de sesión:

```sh
cd backend
uv sync --locked
uv run --locked python -c "import secrets; print(secrets.token_hex(32))"
```

Guarda la clave en `FLASK_SECRET_KEY` en tu `.env` y usa `SESSION_COOKIE_SECURE=0` para el HTTP local. Desde `backend/`, aplica las migraciones:

```sh
uv run --locked alembic upgrade head
```

Si quieres una cuenta ficticia para probar la marcación, ejecuta `uv run --locked flask --app asistencia cargar-demo`. El comando crea `demo.trabajador` y pide elegir su contraseña. Si ya existe, conserva la cuenta y su contraseña. Si ya tienes una cuenta en la base, puedes usarla directamente.

Inicia Flask en esa terminal:

```sh
uv run --locked flask --app asistencia run
```

En otra terminal, desde la raíz del repositorio:

```sh
cd frontend
npm ci
npm run dev
```

Abre [http://127.0.0.1:5173](http://127.0.0.1:5173) e ingresa con tu cuenta. Para probar el flujo de un trabajador, marca la entrada y la salida. En **Historial** verás la jornada cerrada con la sede, las horas y la duración.

La pantalla de [estado del sistema](http://127.0.0.1:5173/estado) comprueba la API y PostgreSQL. Vite reenvía `/api` a Flask en `http://127.0.0.1:5000`.

### Gestión administrativa

Con las migraciones aplicadas, ejecuta este comando desde `backend/` para crear la primera cuenta administrativa:

```sh
uv run --locked flask --app asistencia crear-administrador
```

El comando solicita un usuario y una contraseña. Con esa cuenta, abre **Sedes** para registrar una sede y luego **Trabajadores** para crear una cuenta de trabajador con una contraseña inicial y una sede asignada.

Puedes editar los datos del trabajador y cambiar su sede para futuras entradas. Para desactivarlo, primero debe registrar la salida de cualquier jornada abierta. Su historial seguirá disponible y las marcaciones nuevas se rechazarán.

En **Historial**, elige las fechas de inicio y fin y, si hace falta, filtra por trabajador o sede. El período incluye ambas fechas según la hora de entrada en la zona horaria de la empresa. Si una jornada cruza medianoche, aparece en el día en que empezó. El filtro de sede usa la sede registrada en la jornada.

### Verificación

Desde `backend/`:

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked alembic check
uv run --locked pytest
```

Para ejecutar las pruebas de integración, aplica las migraciones a una base PostgreSQL descartable y define `TEST_DATABASE_URL` con su URL `postgresql+psycopg://…`. CI prepara su propia base para esta suite.

Desde `frontend/`:

```sh
npm run lint
npm test
npm run build
```

## Documentación

- [Alcance del MVP](docs/alcance-mvp.md)
- [Requisitos del MVP](docs/requisitos.md)
- [Casos de uso](docs/casos-de-uso.md)
- [Arquitectura y diagramas](docs/arquitectura.md)
- [Estado y siguiente hito](docs/estado-proyecto.md)
