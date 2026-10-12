---
name: bibliografia-jibril
description: Recupera y propone referencias académicas trazables desde Crossref, OpenAlex u ORCID.
agent: Jibril
---

# Bibliografía de Jibril

## Entradas

- Petición de Tet y objetivo del proyecto.
- Rango temporal, países, disciplinas o autores indicados.
- Fuentes de verificación DOI: Crossref, OpenAlex y ORCID, únicamente con `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1`. DOAJ puede complementar metadatos de revista e ISSN bajo el mismo opt-in en la ingesta web; no sustituye la verificación DOI ni determina calidad o relevancia.
- DOI semilla y propuestas de trabajos que lo citan, cuando Tet autoriza consulta pública.
- Contrato del `edge` para evaluar alineación y posible uso de cada fuente.

## Procedimiento

1. Buscar referencias relacionadas con la petición.
2. Conservar una referencia si su DOI aparece verificado en al menos una de las tres fuentes.
3. Registrar la fuente que confirmó el DOI y conservar las demás evidencias disponibles.
4. No presentar referencias sin DOI o sin fuente verificable.
5. Explicar la utilidad técnica de cada referencia sin sustituir el criterio de Tet.
6. Para un PDF proporcionado por Tet, usar su DOI como semilla y revisar los trabajos citantes localizados por OpenAlex; Crossref aporta metadatos/conteos, pero no se debe afirmar que proporciona la lista de citantes.
7. Evaluar cada candidato frente al contrato del `edge` usando solo los metadatos disponibles; distinguir evidencia del abstract de afirmaciones sobre el texto completo.
8. Guardar candidatos en `docs/bibliografia/propuestas/`, nunca en la bibliografía activa. Tet debe aprobar cada DOI antes de incorporarlo o citarlo como fuente del proyecto.
9. Enviar a APIs públicas solo el DOI semilla y metadatos de consulta necesarios, nunca el PDF ni el contrato del proyecto. La evaluación contextual de candidatos se ejecuta con Ollama local.

## Salida

Propuestas con título, autores, año, DOI, OpenAlex ID, estado de revisión, justificación de alineación y posible contexto de uso; la aprobación final corresponde a Tet.
