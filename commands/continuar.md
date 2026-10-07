# Atender una petición de proyecto

La entrada principal ya no requiere el comando `continuar`. Tet expresa una tarea libre y menciona el ID del proyecto de la matriz. Sora resuelve el proyecto registrado en `Elkia.md`, lee su contrato y peticiones, registra la solicitud y llama al especialista apropiado.

Si Tet no identifica un proyecto único, la consola muestra los IDs disponibles y solicita elegir uno. El agente produce una respuesta o artefacto revisable; si la tarea requiere cambiar el alcance, presenta además una propuesta contractual basada en `contract-template.md`. Solo Tet puede aprobar la incorporación al `contract.md` vigente.

Los controles de regresar, guardar, eliminar y salir solo gobiernan la interacción HITL; no sustituyen la petición de trabajo.
