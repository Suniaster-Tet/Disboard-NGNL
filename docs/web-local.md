# Servidor local, relay de artefactos y sincronización web

## Visión general

El módulo `web/server.py` (FastAPI) expone una interfaz HTTP local para:
- Consultar el estado de los edges (`/api/projects`).
- Consultar el workflow persistente por edge (`/api/runs?project=<edge_id>`).
- Iniciar y reanudar el grafo LangGraph (`/api/graph/runs`, `/api/verdict`).
- Revisar el almacén de artefactos (`/api/artifacts`).
- Consultar el estado de Suniaster (`/api/models`).

El endpoint HTTP de artefactos consulta el registro del edge y comprueba el hash
SHA-256 guardado en la bitácora antes de servir cada archivo. El plugin
`disboard_ext/local_artifact_store.py` es una extensión del registro de plugins;
el endpoint HTTP no delega en él.

## Protocolo de relay y seguridad

- **Puerto predeterminado:** `localhost:8000` (o túnel SSH remoto mediante Codespaces).
- **Verificación de integridad:** se recalcula SHA-256 antes de servir archivos;
  el cierre vuelve a verificar archivos y firmas de todas las aprobaciones.
- **Autenticación:** las conexiones no locales requieren Basic Auth por HTTPS.
  En Codespaces y Docker, `DISBOARD_WEB_REQUIRE_AUTH=true`; credenciales y
  origen permitido se configuran mediante secretos, nunca en el repositorio.
- **Proxy:** habilita `DISBOARD_WEB_TRUST_PROXY_HEADERS` solo si el servidor no
  es accesible por otra ruta y el proxy confiable reenvía `X-Forwarded-Proto`.
- **CSRF:** las mutaciones rechazan `Sec-Fetch-Site: cross-site` y orígenes
  ajenos al host solicitado o a `DISBOARD_WEB_ALLOWED_ORIGINS`.
- **Checkpointer:** el grafo auxiliar usa `SqliteSaver` de LangGraph mediante
  `web/checkpointer.py`. Los hilos persisten en
  `logs/web_graph_checkpoints.sqlite`; la ruta se puede cambiar con
  `DISBOARD_WEB_CHECKPOINT_DB`.

## Cómo levantar el servidor

```bash
# Con Makefile
make web

# O directamente
uvicorn web.server:app --host 127.0.0.1 --port 8000
