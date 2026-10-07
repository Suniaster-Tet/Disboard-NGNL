#!/usr/bin/env python3
"""
ex_machina_verify.py
--------------------
Diagnóstico estático del entorno Suniaster y Disboard-NGNL (Inspirado en la raza Ex Machina).
Comprueba la existencia de directorios, credenciales gratuitas de IA y dependencias del sistema.
"""
import sys
import importlib
import os
from pathlib import Path

COLOR_PRIMARY = "\033[95m"   # Morado NGNL
COLOR_SECONDARY = "\033[96m" # Rosa/Celeste
COLOR_ACCENT = "\033[93m"    # Dorado
COLOR_SUCCESS = "\033[92m"   # Verde
COLOR_RESET = "\033[0m"

REQUIRED_FOLDERS = [
    "docs",
    "docs/emails"
]

REQUIRED_FILES = [
    "brand_rules.json",
    "exeed_config.json",
    "Elkia.md",
    "contract-template.md",
    "exeed_loader.py",
    "kuhaku_governance.py",
    "stephanie_stylist.py",
    "elkia_architect.py",
    "nirvalen_assistant.py",
    "kuhaku_pipeline.py",
    "disboard_console.py",
    "disboard_sync.sh"
]

REQUIRED_ENV_VARS = [
    "GROQ_API_KEY",
    "GOOGLE_AI_STUDIO_API_KEY"
]

REQUIRED_PACKAGES = [
    "langgraph",
    "groq",
    "google", # google-genai
    "pandas",
    "openpyxl",
    "docx", # python-docx
    "pptx", # python-pptx
    "sympy",
    "requests"
]

def check_folders():
    missing = []
    for f in REQUIRED_FOLDERS:
        if not Path(f).is_dir():
            missing.append(f)
    return missing

def check_files():
    missing = []
    for f in REQUIRED_FILES:
        if not Path(f).is_file():
            missing.append(f)
    return missing

def check_env_vars():
    missing = []
    for v in REQUIRED_ENV_VARS:
        if not os.environ.get(v):
            missing.append(v)
    return missing

def check_packages():
    missing = []
    for p in REQUIRED_PACKAGES:
        try:
            importlib.import_module(p)
        except ImportError:
            missing.append(p)
    return missing

def main():
    print(f"{COLOR_PRIMARY}======================================================{COLOR_RESET}")
    print(f"       🤖 EX MACHINA SYSTEM DIAGNOSTIC (SUNI_VERIFY)  ")
    print(f"{COLOR_PRIMARY}======================================================{COLOR_RESET}\n")

    problems = False

    # 1. Verificar carpetas
    missing_f = check_folders()
    if missing_f:
        print(f"⚠️  [{COLOR_ACCENT}AVISO{COLOR_RESET}] Directorios ausentes:")
        for f in missing_f:
            print(f"    - {f}")
    else:
        print(f"✅ [{COLOR_SUCCESS}OK{COLOR_RESET}] Estructura de carpetas completa.")

    # 2. Verificar archivos maestros
    missing_fi = check_files()
    if missing_fi:
        problems = True
        print(f"🛑 [{COLOR_PRIMARY}FALLO{COLOR_RESET}] Archivos de producción críticos ausentes:")
        for f in missing_fi:
            print(f"    - {f}")
    else:
        print(f"✅ [{COLOR_SUCCESS}OK{COLOR_RESET}] Todos los archivos maestros localizados.")

    # 3. Verificar variables de entorno
    missing_env = check_env_vars()
    if missing_env:
        print(f"⚠️  [{COLOR_ACCENT}AVISO{COLOR_RESET}] Credenciales sin configurar (Consumos libres):")
        for v in missing_env:
            print(f"    - {v} (Se inhabilitarán estas llamadas en el pool de inferencia)")
    else:
        print(f"✅ [{COLOR_SUCCESS}OK{COLOR_RESET}] Variables de entorno de IA configuradas.")

    # 4. Verificar dependencias de Python
    missing_pkgs = check_packages()
    if missing_pkgs:
        print(f"⚠️  [{COLOR_ACCENT}AVISO{COLOR_RESET}] Paquetes de Python ausentes (ejecute pip install -r requirements.txt):")
        for p in missing_pkgs:
            print(f"    - {p}")
    else:
        print(f"✅ [{COLOR_SUCCESS}OK{COLOR_RESET}] Todas las dependencias científicas y de IA instaladas.")

    print(f"\n{COLOR_PRIMARY}======================================================{COLOR_RESET}")
    if problems:
        print(f" 🛑 {COLOR_PRIMARY}RESULTADO: Falló la validación estática de Suniaster. Revise errores.{COLOR_RESET}")
        sys.exit(1)
    else:
        print(f" ✦ {COLOR_ACCENT}RESULTADO: Sistema listo y validado estructuralmente. ¡Aschente! ✦{COLOR_RESET}")
    print(f"{COLOR_PRIMARY}======================================================{COLOR_RESET}")

if __name__ == "__main__":
    main()
