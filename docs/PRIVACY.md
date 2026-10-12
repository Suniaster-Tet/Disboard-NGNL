# Privacidad y ubicación de datos

## Modelo de datos

| Dato | Ubicación habitual | Consideración |
|---|---|---|
| Código, contratos y entregables versionados | Repositorio y carpeta `edge-*` | GitHub recibe lo que se publica explícitamente; no usar Git para fuentes o datos privados. |
| Checkpoints de LangGraph, acceso y uso | `.disboard-local/` o `DISBOARD_DATA_DIR` | SQLite local al proceso anfitrión; los checkpoints no equivalen al almacén científico compartido. |
| Artefactos del relay | `DISBOARD_DATA_DIR/artifacts/<edge>/` | Almacén privado separado del edge; la importación al proyecto es manual. |
| PDF y notas bibliográficas | `edge-*/docs/bibliografia/` | Se excluyen de Git por defecto según las reglas del repositorio; conserva el PDF original como fuente. |
| Credenciales y configuración privada | Variables de entorno/almacén local de secretos | No guardar tokens, llaves o credenciales en el repositorio, prompts o logs. |

Configura `DISBOARD_DATA_DIR` en un directorio privado con permisos adecuados. Protege y cifra las copias de seguridad. Una exclusión de Git no cifra archivos ni protege contra otras personas con acceso al mismo host.

## Salidas a servicios externos

- La interfaz web usa Ollama en `localhost` para inferencia y falla cerrado si no está configurado.
- La consola puede usar proveedores externos solo tras el consentimiento correspondiente; proveedor y destino tienen sus propias políticas de retención.
- Las consultas bibliográficas públicas están deshabilitadas por defecto. `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1` habilita la verificación DOI de Jibril en consola (Crossref/OpenAlex/ORCID) y el enriquecimiento web (Crossref/OpenAlex/DOAJ); OpenAlex recibe además el DOI semilla para buscar trabajos citantes. Se envían DOI, no PDF, contratos ni prompts. Un DOI puede revelar el interés de investigación. El permiso para usar un proveedor de IA es independiente y no habilita estas consultas.
- La consulta al Portal ISSN no está integrada. No se envían datos a ese portal desde el código actual.

HTTPS/VPN protegen el transporte, pero no convierten un servicio remoto en almacenamiento local ni garantizan el borrado en proveedores externos. Revisa el consentimiento y la política institucional antes de enviar datos identificables o confidenciales.

## Límite de Codespaces

Codespaces es una máquina remota. Workspace, archivos, SQLite y procesos que se ejecutan allí permanecen en infraestructura cloud; no están en el disco físico del laptop. El relay permite devolver archivos seleccionados al host privado, pero es manual, no sincroniza el repositorio automáticamente y no elimina la copia remota. Para que los datos permanezcan en el equipo personal, ejecuta allí el backend/agentes y configura allí `DISBOARD_DATA_DIR`; usa la tablet como cliente autenticado.

Más detalles de carga, sesiones, TLS y operaciones están en [LOCAL_WEB.md](LOCAL_WEB.md).
