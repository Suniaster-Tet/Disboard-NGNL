"""Agentes de Disboard-NGNL.

Cada agente vive en su propia carpeta con `agent.py`. La skill del agente
vive en `skills/<nombre-en-ingles>/SKILL.md` y se carga con
`Agent.load_skill()`.
"""

__version__ = "2.0.0"

from agents.base import Agent
from agents.sora.agent import SoraStrategist
from agents.chlammy.agent import ChlammyAuditor
from agents.shiro.agent import ShiroAnalyst
from agents.izuna.agent import IzunaDataEngineer
from agents.dola.agent import StephanieOrchestrator
from agents.fiel_nirvalen.agent import FielNirvalen
from agents.jibril.agent import JibrilScientific

__all__ = [
    "Agent",
    "SoraStrategist",
    "ChlammyAuditor",
    "ShiroAnalyst",
    "IzunaDataEngineer",
    "StephanieOrchestrator",
    "FielNirvalen",
    "JibrilScientific",
]
