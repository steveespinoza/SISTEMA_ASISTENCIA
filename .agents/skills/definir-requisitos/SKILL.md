---
name: definir-requisitos
description: Convierte solicitudes de Sistema de Asistencia en reglas y criterios verificables. Úsala al definir una función, precisar un comportamiento ambiguo o evaluar una personalización de cliente.
---

# Definir requisitos de asistencia

1. Lee `docs/alcance-mvp.md` y comprueba el comportamiento actual si ya existe código. Toma el sistema anterior como referencia cuando la tarea lo indique. Sus reglas particulares requieren una solicitud explícita para incorporarse.
2. Describe el actor, la acción y el resultado visible. Añade permisos, estado previo y casos de rechazo cuando cambien el comportamiento. Formula los criterios como ejemplos observables.
3. Identifica qué decisiones están confirmadas. Resuelve detalles técnicos reversibles con el contexto y deja constancia de los supuestos relevantes. Si una decisión de negocio sin respuesta cambia permisos, cálculos, historial o alcance, pregunta por esa decisión concreta y avanza con lo que puedas definir.
4. Para personalizaciones, usa configuración si solo cambia un parámetro de una regla ya definida. Si se pide un flujo distinto, define qué módulo lo incorpora y cómo se conserva el flujo base. Considera una abstracción compartida cuando aparezcan variantes reales.

Ejemplo: ante «agrega tolerancia», define a qué personas se aplica, cuál es la hora programada, cómo se trata el minuto del límite y desde cuándo rige. Si la solicitud es solo un plan, entrega criterios y decisiones abiertas.
