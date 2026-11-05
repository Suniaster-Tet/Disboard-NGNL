# ADR 0001 — Uso de LangGraph para el grafo web

## Contexto

El dashboard web necesita un flujo multiagente con pausas HITL y persistencia
del estado del hilo. El README §2.2 especifica un patrón supervisor (Sora
enruta a Jibril/Shiro/Chlammy y estos devuelven el control) con aprobación de
Tet mediante `interrupt/resume`.

## Decisión

Adoptar **LangGraph** (`langgraph>=0.2.0,<0.4.0`) con:

- `StateGraph(OverallState)` como tipo de estado.
- `interrupt()` en el nodo HITL para pausar el grafo.
- `WebCheckpointer` (adaptador sobre `core/checkpointer.py`) para persistir el
  hilo con `CHECKPOINTER_BACKEND=memory|postgres`.

## Consecuencias

- **Positivas:** patrón supervisor nativo, `interrupt/resume` documentado,
  integración con LangChain (que ya usamos para los modelos de Suniaster),
  checkpointer durable sin reescribir el grafo.
- **Negativas:** dependencia adicional (LangGraph + LangChain), curva de
  aprendizaje, necesidad de fijar versiones para evitar rupturas.

## Alternativas descartadas

- **Implementación manual del grafo:** más código, más bugs, sin `interrupt`.
- **Orquestadores propietarios (ej. AutoGen, CrewAI):** menos control sobre
  HITL y checkpointer, dependencias más pesadas.
