# Idea semilla: Análisis de redes de colaboración científica

## Pregunta

¿Cómo se distribuyen las colaboraciones científicas en un área de investigación
determinada, y qué papel juegan los autores con mayor centralidad?

## Contexto

Se dispone de un conjunto de publicaciones (DOI semilla) y se quiere:

- Extraer metadatos de autores y coautorías.
- Construir una red de colaboración.
- Calcular métricas de centralidad (grado, intermediación, cercanía).
- Visualizar la red y generar un informe reproducible.

## Requisitos

- Los DOIs deben verificarse en Crossref/OpenAlex/ORCID.
- El código debe ser reproducible (semillas fijas, dependencias versionadas).
- El informe debe incluir la metodología y los resultados.
