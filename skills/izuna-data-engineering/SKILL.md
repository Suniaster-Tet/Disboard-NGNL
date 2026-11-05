---
name: izuna-data-engineering
description: Inspecciona, limpia y valida datos tabulares con reglas explícitas y trazabilidad.
agent: Izuna Hatsuse
---

# Ingeniería de datos de Izuna Hatsuse

## Entradas

- Archivos de datos autorizados por Tet.
- Esquema, aliases, tipos, columnas requeridas y reglas de calidad aprobados
  por Tet.
- Límites de memoria, privacidad y destino de salida del proyecto.

## Procedimiento

1. Inspeccionar formatos y encabezados sin cargar datos innecesarios en
   prompts.
2. Aplicar primero lectura, mapeo y validaciones deterministas locales
   (`tools/data_loader.py`).
3. No inferir equivalencias semánticas de columnas sin aprobación; reportar
   ambigüedades.
4. Rechazar columnas requeridas ausentes, colisiones, claves duplicadas y
   conversiones inválidas.
5. Registrar fuente, esquema aplicado, conteos y advertencias sin copiar filas
   sensibles al log.
6. Mantener intactos los archivos de entrada y no publicar datos remotos.
7. Alimentar la base tensorial (`agents/izuna/tensor_db.py`) con metadatos
   validados por Tet.

## Salida

Dataset reproducible bajo el esquema autorizado, informe de validación y
hashes/metadatos de procedencia.

## Límites

- No envía datos sensibles a APIs externas.
- No aprueba esquemas: Tet los aprueba.
