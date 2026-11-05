# Doubt-Driven Development (DDD / Revisión adversarial)

## Descripción

Chlammy Zell actúa como crítica adversarial de contexto fresco. Antes de que
cualquier entregable llegue a Tet para la firma HITL, Chlammy intenta
activamente encontrar fallos de casos límite, supuestos no declarados y vacíos
lógicos.

## Flujo

1. **Envío**: Shiro o Jibril producen un artefacto candidato.
2. **Crítica adversarial**: Chlammy Zell evalúa:
   - Consistencia matemática / física
   - Excepciones no controladas y condiciones de frontera
   - Precisión de citas y verificación de DOI
3. **Reporte**: Chlammy genera un registro de incidencias en
   `edges/<edge-id>/docs/audit/`.
4. **Resolución**: Shiro corrige los fallos identificados antes de presentar
   a Tet.

## Aplica a

- Chlammy (crítica)
- Shiro (corrección)
- Jibril (verificación de citas)
