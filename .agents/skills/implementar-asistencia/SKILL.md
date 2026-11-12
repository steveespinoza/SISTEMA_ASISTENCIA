---
name: implementar-asistencia
description: Guía cambios de código, API y persistencia de Sistema de Asistencia según los límites del monolito modular y las reglas de marcación.
---

# Implementar cambios en asistencia

- Ubica el caso de uso y sus puntos de entrada existentes. Conserva los contratos y el comportamiento que quedan fuera del requisito. Reutiliza lógica del módulo cuando sus invariantes coincidan.
- En la API, valida la forma de la solicitud y delega al caso de uso. Aplica autorización y reglas de negocio en el backend. Mantén las dependencias de Flask y SQLAlchemy fuera de las reglas de dominio. En React, conserva la lógica de presentación y muestra estados y errores a partir del contrato de la API.
- Usa funciones y tipos con una responsabilidad concreta. Introduce una interfaz cuando aísle un límite real, como el reloj o la persistencia de un caso de uso, o cuando haya implementaciones que deban intercambiarse.
- En marcaciones, toma la hora del servidor y conserva la sede de la jornada. Si el cambio afecta concurrencia o reintentos, haz cumplir la consistencia en PostgreSQL y define el límite de la transacción que registra el efecto y el resultado del reintento. Conserva el historial al modificar entidades relacionadas.
- Si cambia el esquema, incluye la migración y considera los datos existentes. Si el cambio establece un precedente difícil de revertir, como mover la responsabilidad de un módulo o cambiar el modelo de despliegue, registra el contexto, la decisión y su consecuencia en un registro de decisión de arquitectura (ADR).
- Mantén fuera del código base las particularidades de clientes que la tarea no incorpore. Cuando sí se incorporen, encapsúlalas en el módulo responsable y conserva la configuración base.
