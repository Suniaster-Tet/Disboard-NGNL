# Edge de ejemplo: `edge-example`

Este edge demuestra el flujo mínimo de Disboard-NGNL.

## Estructura

```text
edge-example/
├── contract.md        # Plan aprobado por Tet
├── log.jsonl          # Registro de eventos (generado en runtime)
├── seed.md            # Idea semilla original
├── artifacts/         # Entregables de los agentes
└── out/               # Salidas finales
```

## Flujo

1. **Tet** propone la idea semilla (`seed.md`).
2. **Sora** genera el plan y lo registra en `contract.md`.
3. **Tet** aprueba el contrato (firma HMAC en el log).
4. **Jibril** enriquece la bibliografía y verifica DOIs.
5. **Shiro** escribe el código y los cálculos.
6. **Chlammy** audita la alineación contra el contrato.
7. **Tet** revisa el resultado y aprueba el cierre.

## Cómo usarlo

```bash
# Desde la raíz del repositorio
python scripts/init_edge.py --seed examples/edge-example/seed.md --titulo "Edge de ejemplo"
```

O desde la consola:

```bash
disboard start --seed examples/edge-example/seed.md
```
