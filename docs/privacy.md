# Privacidad en Disboard-NGNL

> Documento arquitectónico. Complementa a `privacy/prompts_policy.md` (política
> operativa) y al README §3 (Protección de datos).

## Principios

1. **Local-first.** El equipo núcleo ejecuta el backend, los agentes, las bases
   de datos y los artefactos. Los clientes solo consumen interfaz o terminal.
2. **Filtrado centralizado.** Todos los prompts externos pasan por
   `privacy/filters.py`. Fiel Nirvalen reexporta ese filtro en
   `agents/fiel_nirvalen/privacy_filter.py`.
3. **Cálculos locales.** Shiro e Izuna ejecutan operaciones sensibles en el
   host. Solo los metadatos necesarios viajan a APIs externas.
4. **DOI públicos.** Jibril envía DOIs a Crossref/OpenAlex/ORCID, pero nunca el
   PDF ni el contrato del proyecto.
5. **Wolfram condicionado.** Si `WOLFRAM_API_KEY` falta, Suniaster asigna a
   Shiro un proveedor alternativo y Tet valida el resultado.
6. **Modo estricto.** `PRIVACY_STRICT=true` (por defecto) aplica patrones extra
   (DNI, IBAN, URL con token). En `false`, solo patrones base (email, teléfono,
   tarjeta).

## Datos que salen del host

| Servicio | Qué se envía | Qué NO se envía |
|---|---|---|
| Groq / Google AI Studio / OpenAI / Anthropic / DeepSeek | Prompt filtrado, metadatos mínimos | Datos sensibles sin filtrar |
| Crossref / OpenAlex / ORCID | DOIs y metadatos de consulta | PDF, contrato, contenido del edge |
| Wolfram | Expresiones simbólicas | Datos sensibles, contrato |
| Cloudflare Tunnel | Tráfico HTTPS del dashboard (si se habilita) | Nada adicional (es un proxy) |

## Almacenamiento local

- `edges/<id>/log.jsonl` — log estructurado por edge.
- `edges/<id>/contract.md` — contrato aprobado por Tet.
- `edges/<id>/artifacts/` — entregables con hash SHA-256.
- `logs/graph_trace.jsonl` — trazabilidad del grafo web.
- `logs/tensor_db.jsonl` — base tensorial de Izuna.
- `logs/disboard_checkpoints.db` o Postgres — checkpointer durable.

## Verificación

- `privacy.filters.is_safe(text)` comprueba si un texto contiene patrones sensibles.
- `privacy.filters.filter_sensitive_data(text)` filtra antes de escribir en log o prompt.
- `privacy.filters.filter_dict(data)` filtra diccionarios antes de enviarlos.

## Referencias

- `privacy/prompts_policy.md` — política operativa.
- `docs/architecture.md` — arquitectura general.
- `docs/agent_roles.md` — roles y analogías.
