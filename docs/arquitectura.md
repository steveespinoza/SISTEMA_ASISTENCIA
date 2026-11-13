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

## Modelo de datos de marcación

```mermaid
erDiagram
    CUENTA o|--o| TRABAJADOR : vincula
    SEDE ||--o{ TRABAJADOR : asignacion_actual
    SEDE ||--o{ JORNADA : sede_registrada
    TRABAJADOR ||--o{ JORNADA : realiza
    CUENTA ||--o{ SOLICITUD_MARCACION : envia
    JORNADA o|--o{ SOLICITUD_MARCACION : resultado

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
        string nombre
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
        timestamptz salida "Vacía si no se registró la salida"
        boolean sin_salida "Marca una jornada vencida"
        text foto_entrada "Clave del objeto S3, si hay foto"
        text foto_salida "Clave del objeto S3, si hay foto"
    }

    SOLICITUD_MARCACION {
        uuid cuenta_id PK, FK
        uuid clave_reintento PK
        uuid jornada_id FK "Opcional si se rechaza la marcación"
        string operacion
        smallint estado_http
        jsonb resultado "Respuesta original"
    }
```

La sede de la jornada se registra al abrirla. Las consultas muestran **Sin salida** para una jornada anterior al día actual que sigue sin hora de salida. Antes de procesar una nueva marcación o una desactivación, el servicio bloquea la fila del trabajador y marca como vencida su jornada pendiente de un día anterior. La misma transacción comprueba el límite de una entrada por día y conserva el resultado de la solicitud. El índice único parcial permite una sola jornada pendiente por trabajador y excluye las jornadas marcadas sin salida.

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
    alt La operación ya tiene resultado
        BD-->>API: Resultado original
        API-->>UI: Devuelve la respuesta original
    else Primera solicitud válida
        API->>BD: Registra la jornada y el resultado en una transacción
        BD-->>API: Confirma la operación
        API-->>UI: Devuelve la jornada y la hora registrada
    else La operación incumple una regla
        API->>BD: Guarda el rechazo para esa clave
        API-->>UI: Devuelve el motivo del rechazo
    end
    UI-->>T: Muestra la confirmación o el error
```

Si la respuesta se pierde, la interfaz conserva la clave para repetir la misma operación. La [primera migración](../backend/migrations/versions/20261112_0001_crear_tablas_de_asistencia.py) crea las tablas y el índice de jornadas abiertas.

En una instalación con S3, la API comprueba la jornada y los permisos antes de subir la foto. Luego guarda su clave junto con la marcación y el resultado del reintento en PostgreSQL. La clave en S3 depende de la cuenta, la solicitud y la imagen normalizada. Esto permite recuperar una carga previa si se pierde la respuesta de S3. Si PostgreSQL no confirma la transacción después de una carga exitosa, la foto puede quedar sin referencia hasta que se reintente con el mismo archivo. El acceso al objeto requiere un enlace temporal emitido tras verificar el acceso a la jornada.
