# Disboard-NGNL

Disboard coordina proyectos científicos y de software mediante una consola y una interfaz web local. Los agentes preparan planes y borradores; Tet conserva la decisión final sobre cambios, datos y entregables (*human-in-the-loop*). La arquitectura distingue capacidades implementadas de objetivos pendientes y documenta expresamente los límites de privacidad de Codespaces.

## Índice

- [Arquitectura y estado verificable](docs/architecture.md): flujos, módulos, persistencia y criterios de calidad.
- [Stack técnico](docs/STACK.md): librerías por capa, APIs y decisiones entre SQLite, DuckDB y Podman.
- [Operación](docs/OPERATIONS.md): instalación, comandos, web local y relay manual.
- [Privacidad](docs/PRIVACY.md): modelo y ubicación de datos, proveedores externos y límites de Codespaces.
- [Roles y skills](docs/ROLES.md): responsabilidades y skills de los ocho agentes.
- [Guía web detallada](docs/LOCAL_WEB.md): TLS/VPN, configuración, relay y flujos bibliográficos.
- [Catálogo de skills](skills/README.md): convención y cobertura de instrucciones por agente.

## Inicio rápido

Requiere Python 3.12 y Git. Para inferencia local, instala Ollama y un modelo compatible.

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.txt
python disboard_console.py
```

Para iniciar la web local: `python disboard_web.py`. La configuración para acceso desde otros dispositivos y transferencia de archivos está en [Operación](docs/OPERATIONS.md); no expongas el servicio a Internet sin TLS y controles de acceso.

## Alcance

La consola puede generar archivos sujetos a aprobación humana. La web local produce borradores y usa SQLite para checkpoints y datos operativos; no equivale a un almacén científico compartido. Las consultas DOI públicas están deshabilitadas por defecto y requieren opt-in explícito. Consulta [arquitectura](docs/architecture.md) y [privacidad](docs/PRIVACY.md) antes de tratar datos sensibles.

## Apéndice: lore

El marco narrativo del tablero toma inspiración de *No Game No Life*: las reglas y los juegos son una metáfora para expresar decisiones, revisión y autoridad humana. No modifica las instrucciones técnicas ni los controles del sistema. «Declara tu jugada, mide tus cómputos y que comience la partida».