---
name: verificar-cambios
description: Verifica cambios funcionales, de configuración o de esquema en Sistema de Asistencia. Úsala antes de entregar un cambio o al revisar un diff para detectar regresiones.
---

# Verificar cambios de asistencia

Parte del requisito y del diff. Revisa el punto de entrada habitual y selecciona las comprobaciones que correspondan al cambio.

| Si cambia… | Comprueba… |
| --- | --- |
| Entrada, salida o historial | Flujo normal y regresión concreta. Considera reintentos, concurrencia, medianoche y conservación de historial según lo modificado. Usa un reloj fijo en pruebas de tiempo. |
| Permisos o visibilidad | Una operación permitida y una denegada. Cuando aplique, incluye acceso a registros de otro trabajador o a una sede fuera del alcance. |
| Esquema o consistencia transaccional | Migración sobre PostgreSQL descartable y restricciones reales. Para una migración nueva, comprueba la creación desde cero y la actualización desde el esquema anterior con datos representativos. |
| Interfaz de marcación | Recorrido relevante desde la interfaz y estados de carga, error o confirmación que cambien. |
| Configuración o publicación | Valores de ejemplo ficticios y ausencia de secretos o datos de clientes en el diff y en la evidencia que se compartirá. |

Usa los comandos disponibles en el repositorio o en CI. Ejecuta primero las comprobaciones cercanas al cambio y amplía según el impacto. Añade una prueba cuando cubra una regresión relevante que la suite todavía no comprueba. Si revisas un diff, indica archivo, escenario e impacto para cada hallazgo accionable.

Registra los comandos realmente ejecutados, sus resultados y lo que quedó sin comprobar. Si falta una dependencia o un entorno, identifica qué validación queda pendiente.
