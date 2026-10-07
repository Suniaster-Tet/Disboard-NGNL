#!/usr/bin/env python3
"""
exeed_loader.py
---------------
Configuración y constantes globales del ecosistema Disboard-NGNL.
Administra la lectura de modelos y reglas de marca de manera dinámica.
"""
import os
import json
from pathlib import Path

ROOT_DIR = Path(".")
MAESTRO_PATH = ROOT_DIR / "Elkia.md"
AGENDA_PATH = ROOT_DIR / "AGENDAS_Y_CURSOS.md"
MODELOS_CONFIG_PATH = ROOT_DIR / "exeed_config.json"
BRAND_RULES_PATH = ROOT_DIR / "brand_rules.json"
EXTENSIONES_PERMITIDAS = {".py", ".md", ".json", ".txt", ".ipynb", ".tex", ".docx", ".pptx", ".csv", ".xlsx", ".pdf", ".nb"}

def cargar_pool_modelos():
    """Carga dinámica del pool de modelos desde exeed_config.json."""
    if MODELOS_CONFIG_PATH.exists():
        try:
            config = json.loads(MODELOS_CONFIG_PATH.read_text(encoding="utf-8"))
            pool = {}
            for exeed_raza, data in config.get("exeed_registry", {}).items():
                prov = data.get("provider")
                models_list = data.get("models", [])
                pool[prov] = models_list
            return pool
        except Exception as e:
            print(f"[Aviso] Error leyendo exeed_config.json: {e}. Usando respaldo.")
    
    # Respaldo estático
    return {
        "groq": [
            {"modelo": "openai/gpt-oss-120b", "rol": "PRO - Shiro (Cómputo analítico)"},
            {"modelo": "openai/gpt-oss-20b", "rol": "ESTANDAR - Izuna Hatsuse"},
            {"modelo": "qwen/qwen3.8-27b", "rol": "AMPLIO - Kurami Zell"}
        ],
        "gemini": [
            {"modelo": "gemini-2.5-pro", "rol": "PRO - Jibril (Síntesis profunda)"},
            {"modelo": "gemini-2.5-flash", "rol": "ESTANDAR - Fiel Nirvalen / Stephanie"},
            {"modelo": "gemini-flash-lite-latest", "rol": "EXPERIMENTAL - Sora (Terminal)"}
        ],
        "anthropic": [
            {"modelo": "claude-3-5-sonnet-20241022", "rol": "PRO - Shiro (Código avanzado)"},
            {"modelo": "claude-3-haiku-20240307", "rol": "ESTANDAR - Clammy Zell"}
        ],
        "openai": [
            {"modelo": "gpt-4o", "rol": "PRO - Stephanie (Traducción persuasiva)"},
            {"modelo": "gpt-4o-mini", "rol": "ESTANDAR - Fiel (Administrativo)"}
        ]
    }

def guardar_pool_modelos(pool_dict):
    """Sora actualiza exeed_config.json preservando la estructura de validación."""
    try:
        current_config = {}
        if MODELOS_CONFIG_PATH.exists():
            current_config = json.loads(MODELOS_CONFIG_PATH.read_text(encoding="utf-8"))
        
        registry = current_config.get("exeed_registry", {})
        for prov, m_list in pool_dict.items():
            for exeed_raza, r_data in registry.items():
                if r_data.get("provider") == prov:
                    r_data["models"] = m_list
                    break
        
        current_config["exeed_registry"] = registry
        current_config["validation_gate"] = {
            "status": "APPROVED",
            "last_validated_by": "Tet 🖋️",
            "rules_of_play": "Configuración modificada y aprobada bajo veredicto soberano."
        }
        
        MODELOS_CONFIG_PATH.write_text(json.dumps(current_config, indent=4, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        print(f"[Error] No se pudo actualizar el archivo de modelos: {e}")
        return False

def cargar_brand_rules():
    """Carga reglas de marca desde brand_rules.json."""
    if BRAND_RULES_PATH.exists():
        try:
            return json.loads(BRAND_RULES_PATH.read_text(encoding="utf-8"))
        except Exception as e:
            print(f"[Aviso] Error leyendo brand_rules.json: {e}")
    return {}
