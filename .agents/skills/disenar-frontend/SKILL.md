---
name: disenar-frontend
description: Diseña y revisa pantallas, flujos y componentes de Sistema de Asistencia. Úsala al definir la experiencia móvil de marcación, las vistas administrativas o la accesibilidad de la interfaz.
---

# Diseñar el frontend de asistencia

## Flujos por rol

- **Trabajador.** Diseña primero para móvil. Muestra la sede y el estado de la jornada junto a la acción disponible, «Registrar entrada» o «Registrar salida». Tras la confirmación de la API, muestra qué marcación quedó registrada y a qué hora, en la zona horaria de la empresa.
- **Administrador.** Prioriza el historial y la gestión de personal y sedes. En el historial, muestra los filtros activos y distingue jornadas abiertas y cerradas con texto. En pantallas estrechas, conserva el acceso a trabajador, sede, entrada, salida y estado.
- Lee `docs/alcance-mvp.md` para definir los flujos. Incorpora pasos de GPS, fotos o kiosco cuando el requisito incluya esa extensión.

## Estados y accesibilidad

- Diseña los estados de carga, confirmación, error, lista vacía y resultado sin coincidencias según el flujo. Explica con texto qué ocurrió y qué puede hacer la persona.
- En marcación, muestra que el envío está en curso y evita un segundo envío mientras se resuelve. Si se pierde la respuesta, comunica que el resultado está sin confirmar. Al reintentar la misma operación, conserva su identificador de reintento para que la API reconozca la solicitud original.
- Usa controles semánticos con etiquetas visibles, foco perceptible y orden de teclado coherente. Da espacio suficiente a los controles táctiles, asegura el contraste y acompaña el color de estado con texto. Haz que la confirmación y los errores de marcación se anuncien con tecnologías de asistencia.

## Consistencia y revisión

- Mantén una jerarquía clara entre la acción principal y las secundarias. Reutiliza los componentes y los valores de tipografía, espaciado y color del proyecto. Si estás diseñando la primera pantalla, define esos valores para los elementos que ya necesita el flujo.
- Usa textos cortos en español. Incluye un elemento visual cuando ayude a entender datos, orientarse o actuar. Usa datos ficticios en ejemplos y capturas.
- Revisa el flujo afectado en móvil y escritorio y recórrelo con teclado. En marcación, comprueba la confirmación y la recuperación tras un fallo. En historial, comprueba filtros y ausencia de resultados.
