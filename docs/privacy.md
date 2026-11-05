# Privacidad en Disboard-NGNL

> Documento arquitectónico. Complementa a `privacy/prompts_policy.md` (política
> operativa) y al README §3 (Protección de datos).

## Principios

1. **Local-first.** El equipo núcleo ejecuta el backend, los agentes, las bases
   de datos y los artefactos. Los clientes solo consumen interfaz o terminal.
2. **Filtrado explícito.** `privacy/filters.py` ofrece filtros reutilizables;
   no se aplican automáticamente a todos los consumidores. La búsqueda libre
   del dashboard filtra el texto antes de enviarlo a Crossref.
3. **Cálculos locales.** El workflow web actual genera scaffolds y no ejecuta
   cálculos de Shiro ni envía prompts a un proveedor LLM.
4. **DOI públicos.** Jibril envía consultas o DOIs a Crossref/OpenAlex/ORCID;
   no envía PDFs ni contratos en las rutas implementadas.
5. **Wolfram condicionado.** El cliente de Wolfram existe, pero no está
   conectado al workflow del dashboard.
6. **Modo estricto.** `PRIVACY_STRICT=true` (por defecto) aplica patrones extra
   (DNI, IBAN, URL con token). En `false`, solo patrones base (email, teléfono,
   tarjeta).

## Datos que salen del host

| Servicio | Qué se envía | Qué NO se envía |
|---|---|---|
| Groq / Google AI Studio / OpenAI / Anthropic / DeepSeek | No invocados por el workflow actual del dashboard | No aplica a ese flujo |
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
