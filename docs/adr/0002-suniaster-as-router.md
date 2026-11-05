# ADR 0002 — Suniaster como enrutador de modelos

## Contexto

El README §1 y §5.2 establecen que **Suniaster** es el núcleo que asigna el
modelo de IA a cada agente. Los agentes no deben depender de un proveedor
específico, y el sistema debe respetar la política free tier por defecto.

## Decisión

- Cada agente declara su proveedor, modelo y fallback en
  `suniaster/config.yaml`.
- `SuniasterRouter` (`suniaster/router.py`) devuelve un `BaseChatModel` de
  LangChain listo para invocar.
- `SuniasterUpdater` (`suniaster/updater.py`) inspecciona el estado de
  proveedores y modelos, pero **no modifica el config sin aprobación de Tet**.
- Si falta `WOLFRAM_API_KEY`, el router asigna el fallback declarado en
  `defaults.wolfram_fallback_*` (por defecto Google Gemini 2.5 Pro).

## Consecuencias

- **Positivas:** los agentes no conocen al proveedor, solo el modelo. Cambiar
  de proveedor es una línea en `suniaster/config.yaml`. La política free tier
  se aplica de forma centralizada.
- **Negativas:** el router añade una capa de indirección; si un proveedor cae,
  el fallback debe estar bien configurado por agente.

## Alternativas descartadas

- **Proveedor hardcodeado por agente:** viola el requisito de modularidad del
  README §3.
- **Enrutador por reglas simples (sin LangChain):** obliga a reimplementar
  streaming, tools y checkpointer por proveedor.
