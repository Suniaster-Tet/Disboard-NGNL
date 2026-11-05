---
name: stephanie-review
description: Revisa entregables, aplica formato y prepara la presentación HITL sin publicar por cuenta propia.
agent: Stephanie Dola
---

# Revisión de Stephanie Dola

## Entradas

- Entregable existente en `edges/<edge-id>/docs/` o `edges/<edge-id>/src/`.
- Peticiones de Tet.
- Reglas de marca y formato del proyecto.
- Estado de cuotas de proveedores (`SuniasterRouter.describe_agent`).

## Procedimiento

1. Confirmar que el archivo existe y es revisable desde el explorador.
2. Revisar consistencia, formato y trazabilidad.
3. Guardar las correcciones en el archivo del proyecto.
4. Presentar a Tet solo la ruta, estado y resumen, nunca el contenido completo
   en terminal.
5. Aplicar aprobar, modificar, regresar, guardar o eliminar según el veredicto
   de Tet.
6. Si el entregable requiere un proveedor de pago, interrumpir y solicitar
   confirmación explícita a Tet.

## Salida

Entregable revisado y estado HITL pendiente de aprobación, modificación o
rollback.

## Límites

- No envía mensajes.
- No modifica contratos.
- No declara entregables aprobados.
