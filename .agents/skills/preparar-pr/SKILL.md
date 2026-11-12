---
name: preparar-pr
description: Prepara o revisa el título y la descripción de un pull request de Sistema de Asistencia a partir del alcance, el diff y las verificaciones reales.
---

# Preparar un pull request

1. Comprueba la rama y la base de comparación. Si existe el historial, revisa los commits y el diff contra la base. Distingue el trabajo local pendiente de lo que ya está incluido en la rama.
2. Mantén un objetivo revisable por PR. Una funcionalidad puede incluir interfaz, API, migración y pruebas cuando se necesiten para entregar el mismo flujo. Identifica los cambios ajenos y conserva el trabajo del usuario al proponer cómo tratarlo.
3. Escribe un título breve en español que describa el resultado. Usa un prefijo como `feat:`, `fix:` o `docs:` cuando ayude a identificar el cambio. Ejemplo: `fix: conserva la sede histórica de las jornadas`.
4. Usa `.github/pull_request_template.md`. Explica el problema o requisito, qué cambia para el usuario o mantenedor y cómo se verificó. Enlaza una incidencia solo si existe.
5. Para cambios visuales, adjunta evidencia disponible con datos ficticios. Si hay una migración, cambio de configuración o impacto de compatibilidad, documenta los pasos de despliegue y cómo recuperar el servicio si falla. Distingue las verificaciones pendientes de las ejecutadas.

Entrega el título y el cuerpo listos para usar. Abre o actualiza el PR en GitHub cuando el usuario lo solicite.
