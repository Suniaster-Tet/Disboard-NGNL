# Evaluaciones de Disboard-NGNL

Las evaluaciones mínimas del flujo deben comprobar:

1. Un proyecto nuevo crea `contract.md`, `docs/peticiones_tet.md` y una fila dentro de la tabla de `Elkia.md`.
2. La consola muestra todos los proyectos activos del registro `Elkia.md` dentro de los cuatro cuadrantes; metadatos faltantes se señalan como provisionales y los cerrados siguen visibles.
3. La matriz de agenda lee `AGENDAS_Y_CURSOS.md` y permite ordenar pendientes localmente sin llamada de IA.
4. Una petición libre se enruta a un proyecto, creación, correo, informe, agenda, bibliografía u otro asunto.
5. Una petición dirigida a un proyecto se registra y se ejecuta en el mismo ciclo, generando una salida que pasa por HITL.
6. Un cambio contractual sigue `contract-template.md` y solo reemplaza `contract.md` tras aprobación de Tet.
7. Los agentes reciben `docs/peticiones_tet.md` como contexto operativo; el registro no sustituye la ejecución.
8. Las operaciones que mutan agenda y contrato requieren aprobación explícita.
9. Tet puede regresar, guardar, eliminar o salir desde cada interacción HITL.
10. Una petición de correo no envía el texto original al router; solo el correo anonimizado y confirmado puede llegar a Fiel/IA, con destinatario general.
11. Las respuestas aprobadas y las guías importadas se almacenan fuera de Git; al importar se revisa y anonimiza el texto antes de guardarlo.
