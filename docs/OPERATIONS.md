# Operación

## Instalación

Requisitos recomendados: Python 3.12, Git y, para inferencia local, Ollama con un modelo compatible con el equipo.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
```

En Windows PowerShell activa con `.venv\Scripts\Activate.ps1`. Mantén `.venv/` y `.disboard-local/` fuera de Git.

## Comandos principales

```sh
python disboard_console.py
python disboard_web.py
python disboard_users.py add Tet
python disboard_users.py list
```

La consola opera proyectos y presenta artefactos para revisión HITL. La web por defecto escucha en `127.0.0.1:8765`; para usarla desde otro dispositivo configura TLS y una VPN/red privada antes de exponer el servicio. Consulta [LOCAL_WEB.md](LOCAL_WEB.md) para certificados, acceso, configuración de Ollama y navegadores.

Para la web privada local, configura `DISBOARD_OLLAMA_MODEL`, `OLLAMA_BASE_URL=http://127.0.0.1:11434` y, si se requiere, `DISBOARD_DATA_DIR` a una carpeta privada. Las consultas DOI públicas están deshabilitadas por defecto en consola y web. Solo si autorizas enviar DOI a los servicios bibliográficos, habilita explícitamente `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1` en el entorno del proceso; el consentimiento para proveedores de IA no habilita por sí solo estas consultas.

## Relay manual

El relay transfiere artefactos entre un cliente (por ejemplo, Codespaces) y el host privado; no ejecuta agentes remotos ni integra archivos automáticamente en un edge. Configura HTTPS válido en el host y guarda un token aleatorio de al menos 32 caracteres como secreto en ambos entornos. No lo incluyas en Git ni en argumentos visibles.

```sh
export DISBOARD_RELAY_TOKEN="<secreto-local>"
export DISBOARD_RELAY_URL="https://<nombre-privado-del-host>"
python disboard_relay.py list edge-mi-proyecto
python disboard_relay.py upload edge-mi-proyecto results/informe.md ./informe.md
python disboard_relay.py download edge-mi-proyecto inputs/datos.csv ./datos.csv
```

Las transferencias son explícitas, limitadas a 50 MiB, verifican SHA-256 y no sobrescriben el destino. Los archivos de Codespaces continúan en una máquina remota y el relay no borra esa copia. Los detalles de red y credenciales están en [LOCAL_WEB.md](LOCAL_WEB.md); los límites de ubicación de datos se resumen en [PRIVACY.md](PRIVACY.md).
