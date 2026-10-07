#!/usr/bin/env python3
"""
elkia_architect.py
------------------
Inicializador de territorios (workspaces de borde: edge-*) y gestión contractual.
Implementa el podado inteligente de módulos para ahorrar tokens en Suniaster.
Representa el flujo del estado "Nuevo" liderado por Sora.
"""
import os
import re
from pathlib import Path
from datetime import datetime

from disboard_registry import (
    project_by_id,
    project_by_slug,
    read_master_index,
    register_project,
    register_project_content,
)

class ElkiaArchitect:
    def __init__(self, root_dir, maestro_path):
        self.root_dir = Path(root_dir)
        self.maestro_path = Path(maestro_path)

    def crear_nuevo_proyecto(
        self, nombre_sugerido="", titulo_sugerido="", enfoque_inicial=""
    ):
        print(f"\n============================================================\n♟️ [Sora / NUEVO]: Inicialización de un nuevo Proyecto de Borde...\n============================================================\n")
        
        nombre_proyecto = input(
            "1. Ingrese el Nombre del Proyecto "
            f"(Ej: agentes_disboard_ngnl) [{nombre_sugerido}] > "
        ).strip() or nombre_sugerido
        if not nombre_proyecto or nombre_proyecto.lower() == "regresar":
            print("[Sora]: Regresando al menú principal.")
            return ""
        
        slug = f"edge-{nombre_proyecto.lower().replace(' ', '_')}"
        id_proyecto = input("2. Ingrese el ID de Registro del Proyecto (Ej: NGNL-SYS) > ").strip().upper()
        if id_proyecto == "REGRESAR":
            print("[Sora]: Regresando al menú principal.")
            return ""
        if not id_proyecto:
            print("[Sora]: El ID de registro no puede estar vacío.")
            return ""
        maestro_txt = read_master_index(self.maestro_path)
        if project_by_id(maestro_txt, id_proyecto):
            print(f"[Sora]: El ID ya está ocupado en Elkia.md: {id_proyecto}")
            return ""
        if project_by_slug(maestro_txt, slug):
            print(f"[Sora]: La carpeta ya está registrada en Elkia.md: {slug}")
            return ""
        titulo = input(
            f"3. Título Descriptivo amplio del Proyecto [{titulo_sugerido}] > "
        ).strip() or titulo_sugerido
        if titulo.lower() == "regresar":
            print("[Sora]: Regresando al menú principal.")
            return ""

        print(
            "\nDescriba libremente la idea o trabajo inicial "
            "(puede combinar código, investigación, datos, literatura u otros temas)."
        )
        if not enfoque_inicial:
            enfoque_inicial = input("4. Idea o tema inicial de Tet > ").strip()
        if enfoque_inicial.casefold() == "regresar":
            print("[Sora]: Regresando al menú principal.")
            return ""
        
        ruta_carpeta = self.root_dir / slug
        if ruta_carpeta.exists():
            print(f"[Sora]: La carpeta del edge ya existe y no será sobrescrita: {slug}")
            return ""
        ruta_carpeta.mkdir(parents=True, exist_ok=True)
        
        # Estructura del proyecto
        for sub in ["src", "docs"]:
            sub_dir = ruta_carpeta / sub
            sub_dir.mkdir(parents=True, exist_ok=True)
            gitkeep = sub_dir / ".gitkeep"
            if not gitkeep.exists():
                gitkeep.write_text("", encoding="utf-8")
        
        # Leer la plantilla de contrato
        template_file = self.root_dir / "contract-template.md"
        if template_file.exists():
            contrato_txt = template_file.read_text(encoding="utf-8")
        else:
            # Respaldo simple si no existe la plantilla
            contrato_txt = f"# 📜 Contrato de Proyecto: {slug}\n## ID: {id_proyecto}\n## Título: {titulo}\n"
        
        # Reemplazar placeholders
        contrato_txt = contrato_txt.replace("edge-[NombreProyecto]", slug)
        contrato_txt = contrato_txt.replace("[NombreProyecto]", slug)
        contrato_txt = contrato_txt.replace("edge-[slug]", slug)
        contrato_txt = contrato_txt.replace("[ID único]", id_proyecto)
        contrato_txt = contrato_txt.replace("[ID, ej. BIC1]", id_proyecto)
        contrato_txt = contrato_txt.replace("[Ej. BIC1]", id_proyecto)
        contrato_txt = contrato_txt.replace("[Título preciso]", titulo)
        contrato_txt = contrato_txt.replace("[Título descriptivo del proyecto]", titulo)
        contrato_txt = contrato_txt.replace("[Escribir el objetivo principal del proyecto]", titulo)
        contrato_txt = contrato_txt.replace(
            "[Se conserva literalmente como punto de partida]",
            enfoque_inicial or titulo,
        )
                
        # Escribe el contrato local limpio
        local_contract = ruta_carpeta / "contract.md"
        local_contract.write_text(contrato_txt, encoding="utf-8")

        peticiones_file = ruta_carpeta / "docs" / "peticiones_tet.md"
        peticiones_file.write_text(
            "# Peticiones y comentarios de Tet\n\n"
            "Este archivo contiene solicitudes y consultas operativas. "
            "Solo las instrucciones explícitas de agregar o modificar objetivos, metas, "
            "entregables o cronograma se trasladan a `contract.md`.\n",
            encoding="utf-8",
        )
        
        register_project(self.maestro_path, id_proyecto, slug, titulo)
        maestro_txt = read_master_index(self.maestro_path)
        maestro_txt = self.registrar_provenance_proyecto(
            maestro_txt, id_proyecto, slug
        )
        self.maestro_path.write_text(maestro_txt, encoding="utf-8")
        
        print(f"📝 [Sora]: Workspace y Contrato instanciados con éxito en: `{slug}/`")
        return slug

    @staticmethod
    def registrar_proyecto_en_maestro(contenido, id_proyecto, slug, titulo):
        """Compatibility helper for callers that build Elkia content in memory."""
        return register_project_content(
            contenido, id_proyecto, slug, titulo
        )

    @staticmethod
    def registrar_provenance_proyecto(contenido, id_proyecto, slug):
        """Registra el alta una sola vez en la bitácora global de provenance."""
        inicio_marcador = "<!-- PROVENANCE_INICIO -->"
        fin_marcador = "<!-- PROVENANCE_FIN -->"
        if inicio_marcador in contenido and fin_marcador in contenido:
            bloque = contenido.split(inicio_marcador, 1)[1].split(fin_marcador, 1)[0]
            if re.search(rf"^\|\s*\**{re.escape(id_proyecto)}\**\s*\|", bloque, re.IGNORECASE | re.MULTILINE):
                return contenido
            fecha = datetime.now().strftime("%d/%m/%Y")
            fila = (
                f"| **{id_proyecto}** | `{slug}` | ALTA_PROYECTO | Sora | {fecha} | "
                "N/A | CORRECTO | Proyecto registrado en el tablero central |"
            )
            return contenido.replace(fin_marcador, fila + "\n" + fin_marcador, 1)
        return contenido

    def actualizar_contexto_proyecto(self, slug_proyecto, seccion, nuevo_contenido):
        """Queue a requested section update for an AI proposal and Tet's approval."""
        if seccion.lower() not in {"objetivos", "entregables", "cronograma"}:
            return False
        return self.registrar_peticion_tet(
            slug_proyecto,
            f"Propón actualizar la sección {seccion}: {nuevo_contenido.strip()}",
        )

    def registrar_peticion_tet(self, slug_proyecto, peticion):
        peticiones_file = self.root_dir / slug_proyecto / "docs" / "peticiones_tet.md"
        if not peticion.strip():
            return False

        peticiones_file.parent.mkdir(parents=True, exist_ok=True)
        if not peticiones_file.exists():
            peticiones_file.write_text("# Peticiones y comentarios de Tet\n", encoding="utf-8")
        contenido = peticiones_file.read_text(encoding="utf-8").rstrip()
        contenido += f"\n\n- [{datetime.now().strftime('%Y-%m-%d %H:%M')}] {peticion.strip()}"
        peticiones_file.write_text(contenido + "\n", encoding="utf-8")
        return True

    def obtener_peticion_tet(self, slug_proyecto):
        peticiones_file = self.root_dir / slug_proyecto / "docs" / "peticiones_tet.md"
        if not peticiones_file.exists():
            return ""
        return peticiones_file.read_text(encoding="utf-8").strip()

    def agregar_a_seccion_contractual(self, slug_proyecto, seccion, contenido_nuevo):
        """Record a contract change request; never mutate the active contract directly."""
        secciones = {
            "objetivo": "Objetivos y Metas",
            "meta": "Objetivos y Metas",
            "entregable": "Inventario de Productos y Entregables",
            "cronograma": "Cronograma y Avance de Ejecución",
        }
        etiqueta = secciones.get(seccion.lower())
        if not etiqueta or not contenido_nuevo.strip():
            return False
        return self.registrar_peticion_tet(
            slug_proyecto,
            f"Propón agregar a la sección {etiqueta}: {contenido_nuevo.strip()}",
        )
