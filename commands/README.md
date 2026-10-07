# Entrada libre de Elkia

La consola inicia mostrando las matrices de proyectos (desde `Elkia.md`) y agenda general (desde `AGENDAS_Y_CURSOS.md`). Tet escribe una petición natural en el prompt; Sora identifica a qué proyecto o asunto corresponde y la ejecuta con el agente adecuado.

Ejemplos:

- `GRAPHOS: redacta una propuesta para analizar redes de colaboración científica.`
- `Crea un nuevo proyecto para estudiar ...`
- `Prepara un informe general de avances y riesgos.`
- `Redacta un correo para solicitar ...`
- `Agrega a mi agenda una reunión el 2026-10-20 para revisar ...`
- `Revisa el PDF /ruta/articulo.pdf para GRAPHOS y sugiere literatura relacionada.`

`regresar`, `guardar`, `eliminar` y `salir` quedan como controles de interacción, no como tareas de dominio.

Toda petición dirigida a un edge se conserva en `docs/peticiones_tet.md` y se atiende en el mismo ciclo. Los borradores generados se muestran a Tet. Una modificación del alcance produce una propuesta contractual aislada basada en `contract-template.md`; no se cambia el contrato activo hasta recibir aprobación explícita.
