# Test-Driven Development (TDD)

## Descripción

Shiro implementa todo el código siguiendo la metodología Red-Green-Refactor.
Ningún código se integra sin una suite de pruebas que pase.

## Flujo

1. **Red**: Escribir un test unitario que falle y que corresponda a los
   requisitos de `spec.md`.
2. **Green**: Escribir el código mínimo necesario para que el test pase.
3. **Refactor**: Limpiar el código asegurando que los tests sigan en verde.
4. **Validación**: Ejecutar `tools/test_runner.py`.

## Aplica a

- Shiro
