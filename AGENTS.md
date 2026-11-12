# Sistema de Asistencia

Este repositorio contiene la base reutilizable de un sistema de asistencia para empresas. Consulta el [alcance del MVP](docs/alcance-mvp.md) antes de cambiar un flujo o una regla de negocio.

## Contexto y seguimiento

Al empezar una tarea, lee el [estado del proyecto](docs/estado-proyecto.md) para conocer el avance y el siguiente hito. Contrasta el resumen con los archivos y Git cuando afecte a tu tarea.

Actualiza ese archivo en el mismo cambio cuando se complete un hito, cambie una decisión o se desbloquee el siguiente paso. Registra solo avances comprobados y actualiza la fecha. Si cambia el alcance, actualiza también `docs/alcance-mvp.md`. Mantén el estado como un resumen actual y deja el detalle de cada cambio en Git.

## Skills del proyecto

| Si la tarea requiere… | Lee y aplica |
| --- | --- |
| Traducir una solicitud a reglas verificables o decidir si una función pertenece al núcleo | [definir-requisitos](.agents/skills/definir-requisitos/SKILL.md) |
| Escribir o modificar código del producto, contratos de API o persistencia | [implementar-asistencia](.agents/skills/implementar-asistencia/SKILL.md) |
| Diseñar o revisar pantallas, flujos de usuario o componentes visuales | [disenar-frontend](.agents/skills/disenar-frontend/SKILL.md) |
| Verificar un cambio funcional, de configuración o de esquema, o revisar un diff | [verificar-cambios](.agents/skills/verificar-cambios/SKILL.md) |
| Redactar o revisar el título, el alcance o la descripción de un PR | [preparar-pr](.agents/skills/preparar-pr/SKILL.md) |

Una tarea puede usar varias skills. Lee las que correspondan al trabajo solicitado. Mantén los cambios ajenos al objetivo fuera del diff y respeta las ediciones que ya estén en el árbol de trabajo.

Usa datos ficticios en ejemplos, pruebas y capturas. Excluye credenciales, datos personales y material de clientes de los archivos y textos que puedan llegar al repositorio público. Trabaja en local salvo que se solicite una acción remota.
