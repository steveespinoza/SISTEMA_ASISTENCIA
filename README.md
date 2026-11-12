# Sistema de Asistencia

Este proyecto nace de un sistema de asistencia que desarrollé para una empresa con varias sedes. Quiero que cada trabajador pueda marcar su entrada y salida desde el celular y que el administrador pueda revisar quién marcó, a qué hora y en qué sede.

La base técnica ya permite iniciar el frontend, la API y PostgreSQL en local. El flujo de marcación es el siguiente hito.

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

## Desarrollo local

Necesitas Python 3.13, uv, Node.js 24 con npm y Docker con Compose. Compose inicia PostgreSQL 17 y deja el puerto 5432 disponible en la máquina local.

Desde la raíz del repositorio, copia `.env.example` a `.env`. En PowerShell puedes usar `Copy-Item .env.example .env`. Luego inicia PostgreSQL:

```sh
docker compose up -d --wait db
```

En una terminal, instala e inicia la API:

```sh
cd backend
uv sync --locked
uv run --locked alembic upgrade head
uv run --locked flask --app asistencia run
```

En otra terminal, desde la raíz del repositorio:

```sh
cd frontend
npm ci
npm run dev
```

Abre [http://127.0.0.1:5173](http://127.0.0.1:5173). La pantalla de estado comprueba la API y PostgreSQL. Vite reenvía `/api` a Flask en `http://127.0.0.1:5000`.

Para usar una instancia local de PostgreSQL existente, crea una base de desarrollo vacía y ajusta `DATABASE_URL` en `.env` con una URL `postgresql+psycopg://…`.

### Verificación

Desde `backend/`:

```sh
uv run --locked ruff check .
uv run --locked ruff format --check .
uv run --locked alembic check
uv run --locked pytest
```

Para ejecutar también la prueba de integración de la API, define `TEST_DATABASE_URL` en tu terminal con la URL de la base de desarrollo o de una base descartable. CI configura un PostgreSQL propio para ejecutar esa prueba.

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
