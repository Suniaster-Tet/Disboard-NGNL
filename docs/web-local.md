# Servidor local, relay de artefactos y sincronización web

## Visión general

El módulo `web/server.py` (FastAPI) expone una interfaz HTTP local para:
- Consultar el estado de los edges (`/api/projects`).
- Ejecutar el grafo LangGraph (`/api/runs`).
- Revisar el almacén de artefactos (`/api/artifacts`).
- Consultar el estado de Suniaster (`/api/models`).

El relay de artefactos vive en `disboard_ext/local_artifact_store.py` y verifica
los hashes SHA-256 antes de servir cualquier entregable.

## Protocolo de relay y seguridad

- **Puerto predeterminado:** `localhost:8000` (o túnel SSH remoto mediante Codespaces).
- **Verificación de integridad:** el servidor interactúa con
  `disboard_ext/local_artifact_store.py` para verificar los hashes SHA-256 de
  los entregables antes de servirlos.
- **Aislamiento:** el servidor no expone endpoints de modificación de estado
  sin pasar por la validación de firma digital de Tet (`core/hitl.py`).
- **Checkpointer:** el grafo usa `SqliteSaver` de LangGraph mediante
  `web/checkpointer.py`. Los hilos persisten en
  `logs/web_graph_checkpoints.sqlite`; la ruta se puede cambiar con
  `DISBOARD_WEB_CHECKPOINT_DB`.

## Cómo levantar el servidor

```bash
# Con Makefile
make web

# O directamente
uvicorn web.server:app --host 127.0.0.1 --port 8000
