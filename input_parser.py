#!/usr/bin/env python3
"""
input_parser.py
---------------
Parser flexible para interpretar peticiones libres de Tet y mapearlas a acciones.
Usa patrones de expresiones regulares y análisis de palabras clave para extraer intención.
Fallback a entrada estructurada si hay ambigüedad.
"""
import re
from dataclasses import dataclass
from typing import Optional, Dict, List, Any
from enum import Enum


class IntentType(Enum):
    """Tipos de intención detectados en entrada libre."""
    PLAN = "plan"                          # "planificar", "diseñar"
    GENERAR_CODIGO = "generar_codigo"      # "código", "implementar"
    REVISAR = "revisar"                    # "revisar", "auditar"
    CARGAR_PROYECTO = "cargar_proyecto"    # "abrir", "continuar"
    MODIFICAR_CONTRATO = "modificar"       # "cambiar", "actualizar"
    APROBAR = "aprobar"                    # "ok", "listo", "aprobado"
    RECHAZAR = "rechazar"                  # "no", "rechazar", "volver"
    APORTE = "aporte"                      # "pdf", "idea", "archivo", "referencia"
    PETICION_LIBRE = "peticion"            # Cualquier otra cosa
    AMBIGUO = "ambiguo"                    # No se puede clasificar


@dataclass
class ParsedInput:
    """Resultado del parsing de entrada libre."""
    tipo: IntentType
    confianza: float  # 0.0 a 1.0
    accion: Optional[str]  # La acción específica a ejecutar
    contexto: Dict[str, Any]  # Datos extraídos (ID proyecto, archivo, observaciones, etc.)
    mensaje_original: str
    sugerencias: List[str]  # Opciones si hay ambigüedad


class FlexInputParser:
    """
    Interpreta peticiones libres de Tet y mapea a acciones conocidas.
    Si hay ambigüedad, retorna sugerencias para que Tet elija.
    """
    
    def __init__(self):
        # Palabras clave por intención
        self.keywords = {
            IntentType.PLAN: [
                "plan", "planificar", "planear", "estrategia", "hito",
                "cronograma", "objetivo", "meta", "diseñar", "estructura"
            ],
            IntentType.GENERAR_CODIGO: [
                "código", "código", "implementar", "desarrollar", "crear función",
                "escribir", "programar", "algoritmo", "módulo", "clase"
            ],
            IntentType.REVISAR: [
                "revisar", "auditar", "verificar", "controlar", "calidad",
                "test", "validar", "checkear", "revisar", "crítica"
            ],
            IntentType.CARGAR_PROYECTO: [
                "abrir", "continuar", "cargar", "reanudar", "retomar",
                "volver a", "seguir con", "trabajar en"
            ],
            IntentType.MODIFICAR_CONTRATO: [
                "cambiar", "actualizar", "modificar", "editar", "corregir",
                "agregar", "añadir", "eliminar", "borrar", "sustituir"
            ],
            IntentType.APROBAR: [
                "aprobado", "ok", "listo", "sí", "si", "adelante", "confirmar",
                "guardar", "validar", "acepto", "está bien"
            ],
            IntentType.RECHAZAR: [
                "rechazar", "no", "rechazó", "nope", "no quiero", "volver",
                "cancelar", "descartar", "eliminar", "abortar"
            ],
            IntentType.APORTE: [
                "pdf", "referencia", "archivo", "documento", "idea",
                "paper", "artículo", "citar", "bibliografía", "fuente",
                "código fuente", "datos", "dataset"
            ]
        }
    
    def parse(self, entrada: str) -> ParsedInput:
        """
        Analiza entrada libre y retorna estructura ParsedInput con:
        - tipo de intención
        - confianza (0.0-1.0)
        - acción sugerida
        - contexto extraído
        - sugerencias si hay ambigüedad
        """
        entrada = entrada.strip().lower()
        
        if not entrada:
            return ParsedInput(
                tipo=IntentType.AMBIGUO,
                confianza=0.0,
                accion=None,
                contexto={},
                mensaje_original=entrada,
                sugerencias=["Escriba una petición o comando: continuar, plan, aprobar, etc."]
            )
        
        # Detectar intención por palabras clave
        scores = self._puntuar_intenciones(entrada)
        intenciones_ordenadas = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        
        top_intent, top_score = intenciones_ordenadas[0]
        second_intent, second_score = intenciones_ordenadas[1] if len(intenciones_ordenadas) > 1 else (None, 0)
        
        # Si hay ambigüedad (puntajes muy cercanos), marcar como ambiguo
        es_ambiguo = top_score > 0 and abs(top_score - second_score) < 0.3
        
        # Extraer contexto específico
        contexto = self._extraer_contexto(entrada, top_intent)
        
        accion = self._mapear_accion(top_intent, contexto)
        
        sugerencias = []
        if es_ambiguo and second_intent:
            sugerencias = [
                f"¿Se refiere a {top_intent.value} o {second_intent.value}?",
                f"Escriba 'plan', 'código', 'revisar', 'continuar', 'aprobar', etc. para ser más específico."
            ]
            confianza = 0.5
        else:
            confianza = min(top_score / 10, 1.0)  # Normalizar a 0-1
        
        return ParsedInput(
            tipo=top_intent,
            confianza=confianza,
            accion=accion,
            contexto=contexto,
            mensaje_original=entrada,
            sugerencias=sugerencias
        )
    
    def _puntuar_intenciones(self, entrada: str) -> Dict[IntentType, float]:
        """Calcula puntuación para cada tipo de intención basada en palabras clave."""
        scores = {intent: 0.0 for intent in IntentType}
        
        palabras = entrada.split()
        
        for intent, keywords in self.keywords.items():
            for keyword in keywords:
                # Búsqueda parcial (palabra clave como substring)
                if keyword in entrada:
                    scores[intent] += 2.0
                # Búsqueda de palabra completa
                elif any(keyword in palabra for palabra in palabras):
                    scores[intent] += 1.0
        
        return scores
    
    def _extraer_contexto(self, entrada: str, intent: IntentType) -> Dict[str, Any]:
        """Extrae datos específicos según el tipo de intención."""
        contexto = {}
        
        # ID de proyecto (formato: NGNL-SYS, BIC1, etc.)
        proyecto_match = re.search(r'([A-Z0-9]+-[A-Z0-9]+|edge-[\w-]+)', entrada)
        if proyecto_match:
            contexto['proyecto_id'] = proyecto_match.group(1)
        
        # Rutas de archivo (contiene .md, .pdf, .py, etc.)
        archivo_match = re.search(r'(["\']?)([^"\']*\.[a-z]+)\1', entrada)
        if archivo_match:
            contexto['archivo'] = archivo_match.group(2)
        
        # Observaciones/comentarios entre comillas
        comillas_match = re.findall(r'["\']([^"\']+)["\']', entrada)
        if comillas_match:
            contexto['observaciones'] = ' '.join(comillas_match)
        
        # URLs (DOI, enlaces)
        doi_match = re.search(r'10\.\d{4,}/[^\s]+', entrada)
        if doi_match:
            contexto['doi'] = doi_match.group(0)
        
        # Palabras después de "para" indican propósito
        para_match = re.search(r'para\s+([^\.]+)', entrada)
        if para_match:
            contexto['proposito'] = para_match.group(1).strip()
        
        # Rango de urgencia/importancia (si menciona "urgente", "crítico", etc.)
        if any(p in entrada for p in ["urgente", "crítico", "prioritario", "importante"]):
            contexto['urgencia'] = "ALTA"
        elif any(p in entrada for p in ["luego", "después", "cuando pueda", "sin prisa"]):
            contexto['urgencia'] = "BAJA"
        else:
            contexto['urgencia'] = "NORMAL"
        
        return contexto
    
    def _mapear_accion(self, intent: IntentType, contexto: Dict[str, Any]) -> Optional[str]:
        """Mapea intención a una acción ejecutable."""
        mapeo = {
            IntentType.PLAN: "plan_proyecto",
            IntentType.GENERAR_CODIGO: "generar_codigo",
            IntentType.REVISAR: "revisar_entregable",
            IntentType.CARGAR_PROYECTO: "cargar_proyecto",
            IntentType.MODIFICAR_CONTRATO: "modificar_contrato",
            IntentType.APROBAR: "aprobar_entregable",
            IntentType.RECHAZAR: "rechazar_entregable",
            IntentType.APORTE: "registrar_aporte",
            IntentType.PETICION_LIBRE: "guardar_peticion",
            IntentType.AMBIGUO: None
        }
        return mapeo.get(intent)
    
    def parse_veredicto(self, entrada: str) -> Dict[str, Any]:
        """
        Caso especial: parsing de veredicto HITL (APROBAR, MODIFICAR, RECHAZAR).
        Retorna {
            'veredicto': 'aprobar' | 'modificar' | 'rechazar',
            'observaciones': str,
            'confianza': float
        }
        """
        entrada = entrada.strip().lower()
        
        if any(w in entrada for w in ["aprobar", "aprobado", "ok", "sí", "si", "adelante", "guardar"]):
            veredicto = "aprobar"
            confianza = 0.9
        elif any(w in entrada for w in ["modificar", "cambiar", "revisar", "observaciones"]):
            veredicto = "modificar"
            confianza = 0.9
        elif any(w in entrada for w in ["rechazar", "rechazó", "no", "rechazó", "eliminar", "borrar"]):
            veredicto = "rechazar"
            confianza = 0.9
        else:
            # Ambiguo: tratar como comentario libre
            veredicto = "comentario"
            confianza = 0.5
        
        # Extraer observaciones (todo lo que viene después de la palabra clave)
        observaciones = entrada
        for palabra in ["aprobar", "aprobado", "ok", "modificar", "cambiar", "rechazar"]:
            if palabra in entrada:
                idx = entrada.find(palabra)
                observaciones = entrada[idx + len(palabra):].strip()
                break
        
        return {
            "veredicto": veredicto,
            "observaciones": observaciones,
            "confianza": confianza,
            "mensaje_original": entrada
        }
    
    def extract_project_action(self, entrada: str) -> Dict[str, Any]:
        """
        Extrae acciones sobre proyecto de entrada como:
        'continuar NGNL-SYS', 'cargar proyecto BIC1', etc.
        Retorna {
            'accion': 'continuar' | 'cargar' | None,
            'proyecto_id': str,
            'contexto_adicional': str
        }
        """
        entrada = entrada.strip().lower()
        
        # Buscar patrón: verbo + [proyecto/edge] + ID
        match = re.search(
            r'(continuar|cargar|abrir|retomar|reanudar|trabajar en)\s+(?:proyecto\s+)?(?:edge-)?([A-Z0-9\-]+)',
            entrada,
            re.IGNORECASE
        )
        
        if match:
            verbo = match.group(1)
            proyecto_id = match.group(2)
            
            accion_mapeo = {
                "continuar": "continuar",
                "cargar": "cargar",
                "abrir": "cargar",
                "retomar": "continuar",
                "reanudar": "continuar",
                "trabajar en": "continuar"
            }
            
            contexto_adicional = entrada.replace(match.group(0), "").strip()
            
            return {
                "accion": accion_mapeo.get(verbo, "continuar"),
                "proyecto_id": proyecto_id,
                "contexto_adicional": contexto_adicional
            }
        
        return {
            "accion": None,
            "proyecto_id": None,
            "contexto_adicional": entrada
        }
