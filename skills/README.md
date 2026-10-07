# Skills de Kuhaku

Las skills son capacidades reutilizables del ecosistema Disboard-NGNL. Cada skill define su propósito, entradas, procedimiento, salidas y validaciones. No reemplazan a los agentes: Sora, Shiro, Jibril, Stephanie Dola y sus subagentes las activan según la tarea asignada.

## Convención

```text
skills/<nombre>/SKILL.md
```

Una skill debe ser específica, comprobable y agnóstica del proveedor de IA. Cada agente principal y subagente tiene una skill propia. La consola las carga según el responsable del entregable y LangGraph carga las instrucciones de los roles que ejecuta. El contexto del proyecto proviene de `contract.md`, las peticiones operativas de `docs/peticiones_tet.md` y el seguimiento global de `Elkia.md`.

## Cobertura de agentes

| Agente | Skill |
| :--- | :--- |
| Sora | `planificacion-sora` |
| Shiro | `ejecucion-shiro` |
| Stephanie Dola | `revision-stephanie` |
| Fiel Nirvalen | `asistencia-fiel` |
| Izuna Hatsuse | `ingenieria-datos-izuna` |
| Jibril | `bibliografia-jibril` |
| Kurami Zell | `revision-critica-kurami` |
| Clammy Zell | `alineacion-clammy` |
