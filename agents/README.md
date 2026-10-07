# Agentes de Elkia

Los agentes representan responsabilidades narrativas y operativas. Las instrucciones reutilizables viven en `skills/`; los agentes las activan según la tarea.

| Agente | Núcleo | Skills principales |
| :--- | :--- | :--- |
| Sora | Estrategia | `planificacion-sora` |
| Shiro | Código y cómputo | `ejecucion-shiro` |
| Jibril | Bibliografía | `bibliografia-jibril` |
| Stephanie Dola | Revisión y publicación | `revision-stephanie` |
| Fiel Nirvalen | Asistencia administrativa y auditoría | `asistencia-fiel` |
| Izuna Hatsuse | Ingeniería y calidad de datos | `ingenieria-datos-izuna` |
| Kurami Zell | Revisión crítica y restricciones | `revision-critica-kurami` |
| Clammy Zell | Alineación con metas | `alineacion-clammy` |

Los ocho roles del tablero cuentan con skills individuales en `skills/`. La consola selecciona la skill a partir del responsable del entregable; LangGraph carga la skill de cada rol que ejecuta en su grafo local.
