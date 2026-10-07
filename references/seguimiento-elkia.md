# Seguimiento de Elkia

## Fuentes de estado

| Fuente | Propósito | Regla |
| :--- | :--- | :--- |
| `Elkia.md` | Registro maestro y estado global | Una fila por proyecto `edge-*`. |
| `contract.md` | Alcance contractual aprobado | Los agentes proponen cambios con la plantilla; Tet aprueba antes de reemplazarlo. |
| `docs/peticiones_tet.md` | Registro de instrucciones libres de Tet | Sora y el especialista las atienden en el ciclo; el registro no sustituye el resultado. |
| `AGENDAS_Y_CURSOS.md` | Agenda general administrada por Fiel Nirvalen | Sus pendientes aparecen en la matriz; las altas y cambios requieren confirmación de Tet. |
| Bitácora de `contract.md` | Provenance y decisiones | Se actualiza después de acciones relevantes. |
| Archivos en `docs/` y `src/` | Evidencia y entregables | La consola muestra la ruta; el contenido se revisa en el explorador. |

## Estados

```text
NUEVO -> EN_PROCESO -> EN_REVISION -> COMPLETO
  ^          |               |            |
  |          +-- bloquear ---+            |
  +------------- rollback / modificar ---+
```

`COMPLETO` requiere veredicto HITL de Tet. Una petición libre se atiende, pero cualquier cambio del alcance contractual conserva aprobación HITL.
