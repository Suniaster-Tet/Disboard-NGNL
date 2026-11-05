# Política de prompts externos

> Documento operativo. Complementa al README §3 (Protección de datos) y §4.3 (Privacidad).

## Principios

1. **Datos reales nunca salen del host sin filtrado.** Toda comunicación con
   APIs externas (Groq, Google AI Studio, OpenAI, Anthropic, DeepSeek,
   Crossref, OpenAlex, ORCID, Wolfram) pasa por
   `privacy.filters.filter_prompt_external`.
2. **Cálculos sensibles se ejecutan localmente.** Shiro e Izuna ejecutan
   operaciones críticas en el host; solo los metadatos necesarios viajan a la API.
3. **DOIs y metadatos son públicos.** Jibril puede enviar DOIs a Crossref,
   OpenAlex y ORCID, pero nunca el PDF ni el contrato del proyecto.
4. **Wolfram solo recibe expresiones simbólicas.** Si `WOLFRAM_API_KEY` falta,
   Suniaster asigna a Shiro un proveedor alternativo; Shiro declara qué
   proveedor usó y Tet valida el resultado.
5. **Ollama local es el proveedor preferido para evaluación contextual.**
   Cuando Suniaster asigna un modelo local (`ollama`), los datos no salen del host.

## Modo estricto

La variable `PRIVACY_STRICT` (por defecto `true`) controla si se aplican los
patrones extra (DNI, IBAN, URL con token). En `false`, solo se aplican los
patrones base (email, teléfono, tarjeta). Se recomienda dejar `true` salvo en
entornos de prueba con datos sintéticos.

## Patrones filtrados

| Patrón | Reemplazo | Modo |
|---|---|---|
| Correo electrónico | `[EMAIL_PROTECTED]` | Base |
| Teléfono | `[PHONE_PROTECTED]` | Base |
| Tarjeta (13-16 dígitos) | `[CARD_PROTECTED]` | Base |
| DNI/NIE | `[DNI_PROTECTED]` | Estricto |
| IBAN | `[IBAN_PROTECTED]` | Estricto |
| URL con token | `[URL_WITH_TOKEN]` | Estricto |

## Flujo

```text
Tet → agente → filter_prompt_external() → API externa → respuesta → log
