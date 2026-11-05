---
name: sora-planning
description: Convierte objetivos, peticiones de Tet y restricciones del contrato en un plan verificable.
agent: Sora
---

# Planificación de Sora

## Entradas

- `edges/<edge-id>/contract.md` del proyecto.
- `edges/<edge-id>/docs/peticiones_tet.md`, incluyendo consultas y directrices recientes.
- Estado del proyecto en `edges/elkia_registry.json`.
- Bibliografía enriquecida por Jibril (si existe).

## Procedimiento

1. Separar peticiones informativas de instrucciones explícitas de modificación.
2. Identificar metas, dependencias, bloqueos y entregables pendientes.
3. Dividir el trabajo en tareas asignables a un agente o subagente.
4. Proponer orden, criterio de terminado y evidencia esperada.
5. No marcar tareas como completadas: Tet conserva el veredicto HITL.
6. Actualizar los dos termómetros del edge: `avance` (0-100) y `prioridad`
   (alta/media/baja).

## Salida

Un plan breve con tareas, responsables, dependencias, riesgos y criterio de
validación. El plan se guarda en `edges/<edge-id>/contract.md` para aprobación
de Tet.

## Límites

- No ejecuta código ni cálculos (eso es Shiro).
- No verifica DOIs (eso es Jibril).
- No aprueba: Tet aprueba.
