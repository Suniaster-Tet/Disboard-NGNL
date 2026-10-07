---
name: alineacion-clammy
description: Verifica que métodos, código y resultados respondan a metas y entregables aprobados.
agent: Clammy Zell
---

# Alineación de Clammy Zell

## Entradas

- Objetivos, metas, criterios de aceptación y entregables del contrato.
- Plan, código, resultados y observaciones de Tet.

## Procedimiento

1. Relacionar cada resultado con una meta y un criterio de aceptación explícitos.
2. Identificar trabajo fuera de alcance, metas sin evidencia y dependencias incumplidas.
3. No reinterpretar ni modificar el contrato; elevar ambigüedades a Tet.
4. Recomendar la siguiente acción mínima que recupere alineación.
5. No considerar una tarea terminada solo porque se generó un archivo.

## Salida

Matriz meta-evidencia-estado con brechas y acciones pendientes de aprobación humana.
