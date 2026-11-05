# Skills de Disboard-NGNL

Las skills son capacidades reutilizables del ecosistema. Cada skill define su
propósito, entradas, procedimiento, salidas y validaciones. No reemplazan a los
agentes: Sora, Shiro, Jibril, Stephanie Dola y sus subagentes las activan
según la tarea asignada.

## Convención

```text
skills/<nombre-skill>/SKILL.md
skills/methodologies/<nombre-metodologia>.md
```

Una skill debe ser específica, comprobable y agnóstica del proveedor de IA.
Cada agente principal y subagente tiene una skill propia. La consola las carga
según el responsable del entregable y el grafo de LangGraph carga las
instrucciones de los roles que ejecuta. El contexto del proyecto proviene de
`edges/<edge-id>/contract.md`, las peticiones operativas de
`edges/<edge-id>/docs/peticiones_tet.md` y el seguimiento global de
`edges/elkia_registry.json`.

## Cobertura de agentes

| Agente | Skill |
|---|---|
| Sora | `sora-planning` |
| Shiro | `shiro-execution` |
| Stephanie Dola | `stephanie-review` |
| Fiel Nirvalen | `fiel-assistance` |
| Izuna Hatsuse | `izuna-data-engineering` |
| Jibril | `jibril-bibliography` |
| Chlammy Zell (antes Kurami) | `chlammy-alignment` |

## Metodologías

Las metodologías no son skills de agente: son marcos de trabajo que los agentes
aplican según la tarea. Viven en `skills/methodologies/`.

| Metodología | Aplica a |
|---|---|
| `spec-driven-development` | Sora + Tet (contrato antes de código) |
| `test-driven-development` | Shiro (Red-Green-Refactor) |
| `doubt-driven-development` | Chlammy (crítica adversarial antes de HITL) |

## Carga desde código

Los agentes cargan su skill con `Agent.load_skill()`:

```python
from agents.base import Agent
skill = Agent.load_skill("Sora")  # devuelve el contenido de skills/sora-planning/SKILL.md
```

## Agregar una nueva skill

1. Crear la carpeta `skills/<nombre-skill>/`.
2. Añadir `SKILL.md` con frontmatter `name`, `description`, `agent`.
3. Actualizar `agents/base.py` (`SKILL_MAP`) si el agente es nuevo.
4. Actualizar la tabla de cobertura en este README.

## Estructura

```text
skills/
├── README.md
├── sora-planning/SKILL.md
├── shiro-execution/SKILL.md
├── stephanie-review/SKILL.md
├── fiel-assistance/SKILL.md
├── izuna-data-engineering/SKILL.md
├── jibril-bibliography/SKILL.md
├── chlammy-alignment/SKILL.md
└── methodologies/
    ├── spec-driven-development.md
    ├── test-driven-development.md
    └── doubt-driven-development.md
```
