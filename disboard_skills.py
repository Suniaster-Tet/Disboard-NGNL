"""Registro y carga validada de skills para los agentes de Disboard."""
from pathlib import Path


AGENT_SKILLS = {
    "sora": "planificacion-sora",
    "shiro": "ejecucion-shiro",
    "stephanie dola": "revision-stephanie",
    "fiel nirvalen": "asistencia-fiel",
    "izuna hatsuse": "ingenieria-datos-izuna",
    "jibril": "bibliografia-jibril",
    "kurami zell": "revision-critica-kurami",
    "clammy zell": "alineacion-clammy",
}


def cargar_skill(root_dir, agente):
    """Devuelve las instrucciones del agente y falla explícitamente si faltan."""
    nombre = AGENT_SKILLS.get(agente.strip().casefold())
    if nombre is None:
        raise ValueError(f"No existe una skill registrada para el agente {agente!r}.")
    ruta = Path(root_dir) / "skills" / nombre / "SKILL.md"
    if not ruta.is_file():
        raise FileNotFoundError(f"No se encontró la skill requerida: {ruta}")
    return ruta.read_text(encoding="utf-8")
