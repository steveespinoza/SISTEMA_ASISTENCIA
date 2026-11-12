# Arquitectura del MVP

La base actual conecta React, Flask y PostgreSQL. Los diagramas muestran el diseño previsto para incorporar el [flujo de asistencia](casos-de-uso.md). Cada instalación atiende a una empresa con varias sedes y su propia base de datos.

## Componentes

```mermaid
flowchart LR
    T["Trabajador"] --> UI["Interfaz web · React y TypeScript"]
    A["Administrador"] --> UI

    subgraph API["API Flask · un servicio"]
        I["Identidad y permisos"]
        P["Personal y sedes"]
        M["Asistencia"]
        H["Consultas"]
    end

    UI -->|HTTP y JSON| API
    I --> BD[("PostgreSQL")]
    P --> BD
    M --> BD
    H --> BD
```

**Identidad** autentica con nombre de usuario y contraseña y valida la sesión y el rol. **Personal y sedes** mantiene los trabajadores y su asignación vigente. **Asistencia** abre y cierra jornadas. **Consultas** obtiene el historial según los permisos del actor. Las rutas de Flask traducen las solicitudes HTTP y llaman al módulo responsable.

## Modelo de datos propuesto

```mermaid
erDiagram
    CUENTA o|--o| TRABAJADOR : vincula
    SEDE ||--o{ TRABAJADOR : asignacion_actual
    SEDE ||--o{ JORNADA : sede_registrada
    TRABAJADOR ||--o{ JORNADA : realiza
    CUENTA ||--o{ SOLICITUD_MARCACION : envia
    JORNADA ||--o{ SOLICITUD_MARCACION : confirma

    CUENTA {
        uuid id PK
        string nombre_usuario UK
        string hash_contrasena
        string rol
    }

    TRABAJADOR {
        uuid id PK
        uuid sede_id FK
        uuid cuenta_id FK "Opcional y única"
        boolean activo
    }

    SEDE {
        uuid id PK
        string nombre
    }

    JORNADA {
        uuid id PK
        uuid trabajador_id FK
        uuid sede_id FK
        timestamptz entrada
        timestamptz salida "Vacía mientras esté abierta"
    }

    SOLICITUD_MARCACION {
        uuid id PK
        uuid cuenta_id FK
        uuid jornada_id FK
        string clave_reintento
        string operacion
        jsonb resultado "Confirmación original"
    }
```

La sede de la jornada se registra al abrirla. El estado se puede derivar de la hora de salida. PostgreSQL puede imponer una sola jornada abierta por trabajador mediante un índice único parcial sobre las jornadas cuya salida esté vacía. El registro de una marcación exitosa y el resultado asociado a su clave de reintento deben confirmarse en la misma transacción.

## Secuencia de marcación

```mermaid
sequenceDiagram
    actor T as Trabajador
    participant UI as Interfaz web
    participant API as API de asistencia
    participant BD as PostgreSQL

    T->>UI: Selecciona entrada o salida
    UI->>API: Envía la operación con su clave de reintento
    API->>API: Valida la sesión y los permisos
    API->>BD: Busca un resultado para la cuenta y la clave
    alt La misma operación ya se confirmó
        BD-->>API: Resultado original
        API-->>UI: Devuelve la confirmación original
    else Primera solicitud válida
        API->>BD: Registra la jornada y el resultado en una transacción
        BD-->>API: Confirma la operación
        API-->>UI: Devuelve la jornada y la hora registrada
    else La operación incumple una regla
        API-->>UI: Devuelve el motivo del rechazo
    end
    UI-->>T: Muestra la confirmación o el error
```

Si la respuesta se pierde, la interfaz conserva la clave para repetir la misma operación. El modelo es conceptual. La primera migración concretará los nombres, tipos y restricciones de las tablas.
