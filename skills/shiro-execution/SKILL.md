---
name: shiro-execution
description: Implementa código, simulaciones y pruebas con trazabilidad y criterios verificables.
agent: Shiro
---

# Ejecución de Shiro

## Entradas

- Plan de Sora.
- Contrato y peticiones activas de Tet.
- Código y datos existentes del proyecto.
- Bibliografía de Jibril (si aplica).
- Proveedor asignado por Suniaster.

## Procedimiento

1. Inspeccionar solo los archivos necesarios.
2. Implementar el cambio mínimo que satisfaga la tarea.
3. Añadir o ejecutar pruebas focalizadas (`tools/test_runner.py`).
4. Registrar archivos modificados, resultado y bloqueos.
5. Entregar la evidencia en el explorador del proyecto, no volcar el contenido
   completo en la terminal.
6. Si el cálculo requiere Wolfram y no hay `WOLFRAM_API_KEY`, Suniaster asigna
   un proveedor alternativo (por defecto Google Gemini 2.5 Pro); Shiro declara
   qué proveedor usó y Tet valida el resultado.
7. Si Antigravity está disponible (`agy`), usarlo como herramienta opcional
   (`agents/shiro/antigravity_client.py`), no como dependencia exclusiva.

## Salida

Código o simulación reproducible, pruebas ejecutadas y resumen de validación.

## Límites

- No aprueba: Tet aprueba.
- No verifica DOIs: Jibril lo hace.
- No audita alineación: Chlammy lo hace.
