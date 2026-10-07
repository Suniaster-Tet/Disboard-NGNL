#!/usr/bin/env python3
"""
eisenhower_matrix.py
--------------------
Matriz de Eisenhower para clasificación y visualización de tareas.
Clasifica trabajos por urgencia (tiempo) e importancia (estrategia).
Integrada con el registro maestro (Elkia.md) y los contratos locales (contract.md).
"""
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Any
from pathlib import Path
from datetime import datetime
import re


class Cuadrante(Enum):
    """Cuadrantes de la Matriz de Eisenhower."""
    INMEDIATO = "DO_NOW"           # Importante + Urgente
    PLANIFICADO = "SCHEDULE"       # Importante + No Urgente
    DELEGACION = "DELEGATE"        # No Importante + Urgente
    ELIMINAR = "ELIMINATE"         # No Importante + No Urgente


class EstadoTarea(Enum):
    """Estado de ejecución de una tarea."""
    PENDIENTE = "PENDIENTE"
    EN_PROGRESO = "EN_PROGRESO"
    BLOQUEADO = "BLOQUEADO"
    VALIDACION = "VALIDACION_HITL"
    COMPLETADO = "COMPLETADO"
    RECHAZADO = "RECHAZADO"


@dataclass
class Tarea:
    """Representa una tarea u objetivo de proyecto."""
    id: str
    titulo: str
    proyecto_id: str
    descripcion: str
    cuadrante: Cuadrante
    estado: EstadoTarea
    urgencia_score: float  # 0-10 (10 = máxima urgencia)
    importancia_score: float  # 0-10 (10 = máxima importancia)
    fecha_inicio: str  # YYYY-MM-DD
    fecha_vencimiento: str  # YYYY-MM-DD o ""
    responsable: str  # Agente asignado
    artefactos: List[str]  # Archivos asociados
    dependencias: List[str]  # IDs de tareas de las que depende
    notas: str


class EisenhowerMatrix:
    """
    Matriz de Eisenhower dinámica integrada con Disboard-NGNL.
    Lee de Elkia.md y contract.md para construir la matriz de tareas activas.
    """
    
    def __init__(self, root_dir: Path, maestro_path: Path):
        self.root_dir = Path(root_dir)
        self.maestro_path = Path(maestro_path)
        self.tareas: Dict[str, Tarea] = {}
    
    def cargar_tareas_desde_proyecto(self, slug_proyecto: str) -> List[Tarea]:
        """
        Lee contract.md del proyecto y extrae tareas/hitos.
        Retorna lista de Tarea clasificadas por cuadrante.
        """
        contract_path = self.root_dir / slug_proyecto / "contract.md"
        if not contract_path.exists():
            return []
        
        contenido = contract_path.read_text(encoding="utf-8")
        tareas = []
        
        # Buscar sección de entregables/hitos
        entregables_match = re.search(
            r"## .*Inventario de Productos y Entregables.*?\n(.*?)(?=\n## |\Z)",
            contenido,
            re.DOTALL | re.IGNORECASE
        )
        
        if entregables_match:
            seccion = entregables_match.group(1)
            # Extraer items (- [ ] o - [ x])
            items = re.findall(r"- \[([ x])\]\s+(.+?)(?:\n|$)", seccion, re.IGNORECASE)
            
            for i, (completado, titulo) in enumerate(items):
                tarea_id = f"{slug_proyecto}-TASK-{i+1}"
                estado = EstadoTarea.COMPLETADO if completado.lower() == 'x' else EstadoTarea.PENDIENTE
                
                # Clasificar por palabras clave (urgencia/importancia)
                urgencia = self._inferir_urgencia(titulo)
                importancia = self._inferir_importancia(titulo)
                cuadrante = self._calcular_cuadrante(urgencia, importancia)
                
                tarea = Tarea(
                    id=tarea_id,
                    titulo=titulo,
                    proyecto_id=slug_proyecto,
                    descripcion="",
                    cuadrante=cuadrante,
                    estado=estado,
                    urgencia_score=urgencia,
                    importancia_score=importancia,
                    fecha_inicio=datetime.now().strftime("%Y-%m-%d"),
                    fecha_vencimiento="",
                    responsable="",
                    artefactos=[],
                    dependencias=[],
                    notas=""
                )
                tareas.append(tarea)
                self.tareas[tarea_id] = tarea
        
        return tareas
    
    def cargar_todos_proyectos(self) -> Dict[str, List[Tarea]]:
        """Lee Elkia.md y carga tareas de todos los proyectos activos."""
        if not self.maestro_path.exists():
            return {}
        
        contenido = self.maestro_path.read_text(encoding="utf-8")
        
        # Extraer slugs de proyectos (patrón: edge-NombreProyecto)
        slugs = re.findall(r'\b(edge-[\w-]+)\b', contenido)
        
        proyectos_tareas = {}
        for slug in set(slugs):
            tareas = self.cargar_tareas_desde_proyecto(slug)
            if tareas:
                proyectos_tareas[slug] = tareas
        
        return proyectos_tareas
    
    def _inferir_urgencia(self, titulo: str) -> float:
        """
        Infiere urgencia (0-10) basada en palabras clave en el título.
        10 = urgente, crítico, inmediato
        """
        titulo_lower = titulo.lower()
        
        if any(p in titulo_lower for p in ["urgente", "crítico", "ahora", "inmediato", "emergencia"]):
            return 10.0
        elif any(p in titulo_lower for p in ["pronto", "semana", "hoy", "mañana"]):
            return 7.5
        elif any(p in titulo_lower for p in ["próximo", "próximas", "después"]):
            return 5.0
        elif any(p in titulo_lower for p in ["luego", "después", "futuro", "sin prisa"]):
            return 2.5
        
        return 5.0  # Valor por defecto
    
    def _inferir_importancia(self, titulo: str) -> float:
        """
        Infiere importancia (0-10) basada en palabras clave en el título.
        10 = estratégico, fundamental, core
        """
        titulo_lower = titulo.lower()
        
        if any(p in titulo_lower for p in ["principal", "core", "fundamental", "estratégico", "crítico"]):
            return 10.0
        elif any(p in titulo_lower for p in ["importante", "clave", "base", "arquitectura"]):
            return 8.0
        elif any(p in titulo_lower for p in ["validar", "revisar", "verificar"]):
            return 6.5
        elif any(p in titulo_lower for p in ["documentar", "comentar", "cosmético", "menor"]):
            return 3.0
        elif any(p in titulo_lower for p in ["experimental", "exploración", "nice-to-have"]):
            return 2.5
        
        return 5.0  # Valor por defecto
    
    def _calcular_cuadrante(self, urgencia: float, importancia: float) -> Cuadrante:
        """Determina cuadrante basado en scores de urgencia e importancia."""
        umbral = 5.0
        
        if importancia >= umbral and urgencia >= umbral:
            return Cuadrante.INMEDIATO
        elif importancia >= umbral and urgencia < umbral:
            return Cuadrante.PLANIFICADO
        elif importancia < umbral and urgencia >= umbral:
            return Cuadrante.DELEGACION
        else:
            return Cuadrante.ELIMINAR
    
    def renderizar_matriz_ascii(self, proyectos_tareas: Dict[str, List[Tarea]]) -> str:
        """
        Genera una representación ASCII de la matriz de Eisenhower.
        Mostrando todos los proyectos y sus tareas organizadas.
        """
        lineas = []
        lineas.append("\n" + "="*80)
        lineas.append("📊 MATRIZ DE EISENHOWER - Disboard NGNL")
        lineas.append("="*80)
        
        # Agrupar por cuadrante
        por_cuadrante = {cuad: [] for cuad in Cuadrante}
        
        for slug_proyecto, tareas in proyectos_tareas.items():
            for tarea in tareas:
                por_cuadrante[tarea.cuadrante].append((slug_proyecto, tarea))
        
        # 1. INMEDIATO (Importante + Urgente) - DO NOW
        lineas.append("\n🔴 CUADRANTE I: HACER AHORA (Importante + Urgente)")
        lineas.append("-" * 80)
        if por_cuadrante[Cuadrante.INMEDIATO]:
            for slug, tarea in por_cuadrante[Cuadrante.INMEDIATO]:
                estado_icon = self._estado_icon(tarea.estado)
                lineas.append(
                    f"  {estado_icon} [{tarea.id}] {tarea.titulo}\n"
                    f"      📁 {slug} | ⏰ Urgencia: {tarea.urgencia_score:.1f}/10"
                )
        else:
            lineas.append("  ✅ Sin tareas inmediatas")
        
        # 2. PLANIFICADO (Importante + No Urgente) - SCHEDULE
        lineas.append("\n🟡 CUADRANTE II: PLANIFICAR (Importante + No Urgente)")
        lineas.append("-" * 80)
        if por_cuadrante[Cuadrante.PLANIFICADO]:
            for slug, tarea in por_cuadrante[Cuadrante.PLANIFICADO]:
                estado_icon = self._estado_icon(tarea.estado)
                lineas.append(
                    f"  {estado_icon} [{tarea.id}] {tarea.titulo}\n"
                    f"      📁 {slug} | 📋 Importancia: {tarea.importancia_score:.1f}/10"
                )
        else:
            lineas.append("  ℹ️ Sin tareas planificadas")
        
        # 3. DELEGACIÓN (No Importante + Urgente) - DELEGATE
        lineas.append("\n🟠 CUADRANTE III: DELEGAR (No Importante + Urgente)")
        lineas.append("-" * 80)
        if por_cuadrante[Cuadrante.DELEGACION]:
            for slug, tarea in por_cuadrante[Cuadrante.DELEGACION]:
                estado_icon = self._estado_icon(tarea.estado)
                lineas.append(
                    f"  {estado_icon} [{tarea.id}] {tarea.titulo}\n"
                    f"      📁 {slug} | 🎯 Delegable"
                )
        else:
            lineas.append("  ✅ Sin tareas para delegar")
        
        # 4. ELIMINAR (No Importante + No Urgente) - ELIMINATE
        lineas.append("\n⚪ CUADRANTE IV: ELIMINAR (No Importante + No Urgente)")
        lineas.append("-" * 80)
        if por_cuadrante[Cuadrante.ELIMINAR]:
            for slug, tarea in por_cuadrante[Cuadrante.ELIMINAR]:
                estado_icon = self._estado_icon(tarea.estado)
                lineas.append(
                    f"  {estado_icon} [{tarea.id}] {tarea.titulo}"
                )
        else:
            lineas.append("  ✅ Sin tareas prescindibles")
        
        lineas.append("\n" + "="*80)
        lineas.append("Leyenda: 🟢 Pendiente | 🟠 En Progreso | 🔵 Bloqueado | 🟡 Validación | ✅ Completado | ❌ Rechazado")
        lineas.append("="*80 + "\n")
        
        return "\n".join(lineas)
    
    def _estado_icon(self, estado: EstadoTarea) -> str:
        """Retorna icono según estado de tarea."""
        iconos = {
            EstadoTarea.PENDIENTE: "🟢",
            EstadoTarea.EN_PROGRESO: "🟠",
            EstadoTarea.BLOQUEADO: "🔵",
            EstadoTarea.VALIDACION: "🟡",
            EstadoTarea.COMPLETADO: "✅",
            EstadoTarea.RECHAZADO: "❌"
        }
        return iconos.get(estado, "❓")
    
    def actualizar_estado_tarea(self, tarea_id: str, nuevo_estado: EstadoTarea) -> bool:
        """Actualiza el estado de una tarea en el registro interno."""
        if tarea_id in self.tareas:
            self.tareas[tarea_id].estado = nuevo_estado
            return True
        return False
    
    def obtener_tareas_por_proyecto(self, slug_proyecto: str) -> List[Tarea]:
        """Retorna todas las tareas de un proyecto específico."""
        return [t for t in self.tareas.values() if t.proyecto_id == slug_proyecto]
    
    def obtener_tareas_por_cuadrante(self, cuadrante: Cuadrante) -> List[Tarea]:
        """Retorna todas las tareas en un cuadrante específico."""
        return [t for t in self.tareas.values() if t.cuadrante == cuadrante]
