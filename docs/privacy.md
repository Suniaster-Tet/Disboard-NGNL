# Privacidad en Disboard-NGNL

> Documento arquitectónico. Complementa a `privacy/prompts_policy.md` (política
> operativa) y al README §3 (Protección de datos).

## Principios

1. **Local-first.** El equipo núcleo ejecuta el backend, los agentes, las bases
   de datos y los artefactos. Los clientes solo consumen interfaz o terminal.
2. **Filtrado de prompts.** `privacy/filters.py` ofrece filtros reutilizables;
   la inferencia de Sora, Shiro y plantillas y la búsqueda libre de Jibril los
   aplican antes de las llamadas externas. Los patrones conocidos no equivalen
   a un DLP completo; Tet debe revisar la solicitud antes de habilitar modelos.
3. **Modelos gratuitos.** Con `DISBOARD_USE_LLM=true`, Suniaster usa proveedores
   configurados; `allow_paid: false` evita proveedores de pago por defecto.
   Solicitudes y resultados se guardan localmente, pero el prompt filtrado sale
   al proveedor seleccionado.
4. **Ejecución de código.** Shiro redacta código y tests; el dashboard no los
   ejecuta. Tet debe revisar y ejecutar los artefactos en un entorno controlado.
5. **DOI públicos.** Jibril envía consultas bibliográficas filtradas o DOIs a
   Crossref/OpenAlex/ORCID; no envía PDFs ni contratos en las rutas actuales.
6. **Wolfram condicionado.** El cliente existe, pero no está conectado al
   workflow del dashboard actual.
7. **Modo estricto.** `PRIVACY_STRICT=true` (por defecto) aplica patrones extra
   (DNI, IBAN, URL con token). En `false`, solo patrones base (email, teléfono,
   tarjeta).

## Datos que salen del host

| Servicio | Qué se envía | Qué NO se envía |
|---|---|---|
| Groq / Google AI Studio | Prompts filtrados de Sora/Shiro/plantillas si `DISBOARD_USE_LLM=true` | Clave API, archivos del edge y contenido que no esté en el prompt |
| OpenAI / Anthropic / DeepSeek | No usados si `allow_paid: false`; requieren autorización explícita en configuración | Datos del edge fuera del prompt |
| Crossref | Consulta bibliográfica filtrada y DOIs | PDF, contrato, contenido completo del edge |
| OpenAlex / ORCID | DOI verificado | PDF, contrato, contenido completo del edge |
| Wolfram | No invocado por el workflow actual del dashboard | No aplica a ese flujo |
| Cloudflare Tunnel | Tráfico HTTPS del dashboard (si se habilita) | Nada adicional (es un proxy) |

## Almacenamiento local

- `edges/<id>/log.jsonl` — log estructurado por edge.
- `edges/<id>/contract.md` — contrato aprobado por Tet.
- `edges/<id>/artifacts/` — entregables con hash SHA-256.
- `logs/graph_trace.jsonl` — trazabilidad del grafo web.
- `logs/tensor_db.jsonl` — base tensorial de Izuna.
- `logs/web_graph_checkpoints.sqlite` — checkpointer SQLite durable del grafo web.

El contenido del edge y los checkpoints no se cifran en reposo por la aplicación.
Los logs se escriben de forma append-only por el flujo normal, pero un usuario con
acceso al host puede modificarlos; conserva backups y protege el sistema de archivos.

## Verificación

- `privacy.filters.is_safe(text)` comprueba patrones conocidos; no es un DLP completo.
- `privacy.filters.filter_sensitive_data(text)` filtra cuando el llamador lo invoca.
- `privacy.filters.filter_dict(data)` filtra diccionarios cuando el llamador lo invoca.

## Referencias

- `privacy/prompts_policy.md` — política operativa.
- `docs/architecture.md` — arquitectura general.
- `docs/agent_roles.md` — roles y analogías.
