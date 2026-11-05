# Spec-Driven Development (SDD)

## Descripción

No se empieza a codificar sin un `spec.md` aprobado. Sora y Tet deben acordar
objetivos, requisitos, restricciones y no-objetivos antes de que Shiro escriba
código de implementación.

## Flujo

1. **Borrador**: Sora analiza la directriz de Tet y redacta `spec.md` con:
   - Objetivos y entregables
   - No-objetivos
   - Restricciones del sistema
   - Métricas de verificación
2. **Revisión**: Chlammy Zell prueba ambigüedades o casos límite.
3. **Aprobación (HITL)**: Tet revisa y firma `spec.md`.
4. **Ejecución**: Shiro implementa contra `spec.md` usando TDD.

## Aplica a

- Sora (borrador)
- Chlammy (revisión)
- Tet (aprobación)
- Shiro (ejecución)
