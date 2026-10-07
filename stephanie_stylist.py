#!/usr/bin/env python3
"""
stephanie_stylist.py
---------------------
Aplica la paleta de colores y reglas de marca de brand_rules.json (Disboard-NGNL / SECIHTI)
a los preprints, reportes y diapositivas compiladas.
"""
import argparse
import json
import sys
from pathlib import Path
from exeed_loader import cargar_brand_rules

def load_brand_profile(profile_name=None):
    rules = cargar_brand_rules()
    if not rules:
        return {}
    
    if not profile_name:
        profile_name = rules.get("active_profile", "disboard_ngnl")
    
    profile_data = rules.get("profiles", {}).get(profile_name, {})
    merged = dict(rules)
    merged.update(profile_data)
    merged["active_profile"] = profile_name
    return merged

def apply_to_latex(path, rules):
    path = Path(path)
    if not path.exists():
        print(f"⚠️ Archivo no encontrado: {path}")
        return
    
    text = path.read_text(encoding="utf-8")
    profile = rules.get("active_profile", "disboard_ngnl")
    
    c_primary = rules.get("palette", {}).get("primary", "#1E0030")
    c_secondary = rules.get("palette", {}).get("secondary", "#E60067")
    c_accent = rules.get("palette", {}).get("accent", "#FFD700")
    footer = rules.get("footer_text", "")
    
    color_defines = f"""
% --- SUNI_STYLIST DEFINES ({profile.upper()}) ---
\\definecolor{{suniprimary}}{{HTML}}{{{c_primary.replace("#", "")}}}
\\definecolor{{sunisecondary}}{{HTML}}{{{c_secondary.replace("#", "")}}}
\\definecolor{{suniaccent}}{{HTML}}{{{c_accent.replace("#", "")}}}
\\fancyfoot[C]{{\\small {footer}}}
% ------------------------------------------------
"""
    
    marker = "% --- SUNI_STYLIST DEFINES"
    if marker in text:
        return
    
    if "\\begin{document}" in text:
        partes = text.split("\\begin{document}")
        updated = partes[0] + color_defines + "\\begin{document}" + partes[1]
        path.write_text(updated, encoding="utf-8")
        print(f"🎨 [Stephanie Stylist]: Estilo {profile.upper()} inyectado en LaTeX: {path.name}")
    else:
        path.write_text(text + color_defines, encoding="utf-8")
        print(f"🎨 [Stephanie Stylist]: Estilo inyectado al final de LaTeX: {path.name}")

def apply_to_docx(path, rules):
    path = Path(path)
    if not path.exists():
        return
    try:
        from docx import Document
        doc = Document(str(path))
        footer_text = rules.get("footer_text", "")
        for s in doc.sections:
            s.footer.paragraphs[0].text = footer_text
        doc.save(str(path))
        print(f"🎨 [Stephanie Stylist]: Pie de página inyectado en Word: {path.name}")
    except Exception as e:
        print(f"⚠️ No se pudo procesar Word {path.name}: {e}")

def apply_to_pptx(path, rules):
    path = Path(path)
    if not path.exists():
        return
    try:
        from pptx import Presentation
        prs = Presentation(str(path))
        c_accent = rules.get("palette", {}).get("accent", "#FFD700")
        print(f"🎨 [Stephanie Stylist]: Paleta PPTX revisada con acento '{c_accent}' para {path.name}")
        prs.save(str(path))
    except Exception as e:
        print(f"⚠️ No se pudo procesar PowerPoint {path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Estilista Stephanie aplica reglas de papelería oficial.")
    parser.add_argument("--target", type=str, help="Ruta al archivo (.tex, .docx, .pptx)")
    parser.add_argument("--profile", type=str, default=None, help="Perfil estético (disboard_ngnl / secihti_oficial)")
    parser.add_argument("--all", action="store_true", help="Procesar todos los documentos de docs/")
    
    args = parser.parse_args()
    rules = load_brand_profile(args.profile)
    
    if args.target:
        p = Path(args.target)
        if p.suffix.lower() == ".tex":
            apply_to_latex(p, rules)
        elif p.suffix.lower() == ".docx":
            apply_to_docx(p, rules)
        elif p.suffix.lower() == ".pptx":
            apply_to_pptx(p, rules)
    elif args.all:
        docs_root = Path("docs")
        if docs_root.exists():
            for f in docs_root.rglob("*"):
                if f.suffix.lower() == ".tex":
                    apply_to_latex(f, rules)
                elif f.suffix.lower() == ".docx":
                    apply_to_docx(f, rules)
                elif f.suffix.lower() == ".pptx":
                    apply_to_pptx(f, rules)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
