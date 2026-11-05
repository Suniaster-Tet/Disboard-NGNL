# ADR 0003 — Antigravity como herramienta opcional para Shiro

## Contexto

Shiro es el agente ejecutor principal. Su tarea es escribir código, ejecutar
cálculos y entregar artefactos del plan. El README §1 permite que Shiro use la
API de Wolfram (si hay clave) para cálculos simbólicos. Además, el proyecto
puede aprovechar herramientas externas de agentes como Antigravity (CLI `agy`
y SDK `google-antigravity`), pero **no debe depender exclusivamente de ella**.

## Decisión

- Instalar el SDK (`google-antigravity`) y la CLI (`agy`) en el devcontainer
  como herramientas **opcionales**.
- `agents/shiro/antigravity_client.py` expone `is_available()`, `version()` y
  `run(prompt)`. Si `agy` no está disponible, devuelve `None`.
- El `HEALTHCHECK` del contenedor **no** verifica `agy`: su disponibilidad
  depende de Suniaster y de las credenciales, no del contenedor.
- Si el cálculo requiere Wolfram y no hay `WOLFRAM_API_KEY`, Suniaster asigna
  un proveedor alternativo. Shiro declara qué proveedor usó y Tet valida.

## Consecuencias

- **Positivas:** Shiro puede usar Antigravity cuando esté disponible, pero
  sigue funcionando con el proveedor asignado por Suniaster. No hay dependencia
  dura de Antigravity.
- **Negativas:** la imagen del contenedor crece (~100 MB extra). El SDK y la
  CLI deben actualizarse cuando Antigravity publique versiones nuevas.

## Alternativas descartadas

- **Antigravity como proveedor exclusivo de Shiro:** viola el requisito de
  modularidad y free tier del README §1.
- **No instalar Antigravity:** pierde una herramienta útil, pero el flujo
  principal no depende de ella.
