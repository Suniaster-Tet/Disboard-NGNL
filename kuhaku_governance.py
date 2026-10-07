#!/usr/bin/env python3
"""
kuhaku_governance.py
--------------------
Gobierno de IA y Enrutador de Inferencia de 『 』 (Kuhaku).
Soporta Gemini, Groq, Anthropic y OpenAI con semáforos de advertencia para cuotas gratuitas.
Registra la bitácora transaccional directamente en los Markdown locales.
"""
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from exeed_loader import cargar_pool_modelos, guardar_pool_modelos
from disboard_usage import UsageLedger, estimate_tokens

COLOR_PRIMARY = "\033[95m"   # Morado NGNL
COLOR_SECONDARY = "\033[96m" # Rosa/Celeste
COLOR_ACCENT = "\033[93m"    # Dorado
COLOR_SUCCESS = "\033[92m"   # Verde
COLOR_RESET = "\033[0m"

HAS_GROQ = False
try:
    from groq import Groq
    HAS_GROQ = True
except ImportError:
    pass

HAS_GEMINI = False
try:
    from google import genai
    HAS_GEMINI = True
except ImportError:
    pass

HAS_ANTHROPIC = False
try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    pass

HAS_OPENAI = False
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    pass

class KuhakuGovernance:
    def __init__(self, root_dir):
        self.root_dir = Path(root_dir)
        self.modelos_pool = cargar_pool_modelos()
        self.usage_ledger = UsageLedger()
        self.last_usage = None

    def recargar_configuracion_modelos(self):
        self.modelos_pool = cargar_pool_modelos()

    def sora_actualizar_modelo(self, proveedor, nombre_modelo, nuevo_rol, posicion=None):
        self.recargar_configuracion_modelos()
        proveedor = proveedor.lower()
        if proveedor not in self.modelos_pool:
            self.modelos_pool[proveedor] = []
        
        encontrado = False
        for m in self.modelos_pool[proveedor]:
            if m["modelo"].lower() == nombre_modelo.lower():
                m["rol"] = nuevo_rol
                encontrado = True
                break
        
        if not encontrado:
            nuevo_item = {"modelo": nombre_modelo, "rol": nuevo_rol}
            if posicion is not None and 0 <= posicion <= len(self.modelos_pool[proveedor]):
                self.modelos_pool[proveedor].insert(posicion, nuevo_item)
            else:
                self.modelos_pool[proveedor].append(nuevo_item)
        
        exito = guardar_pool_modelos(self.modelos_pool)
        if exito:
            print(f"\n[SORA OBERON]: exeed_config.json actualizado dinámicamente con '{nombre_modelo}' bajo '{proveedor}'.")
        return exito

    def _llamar_proveedor(self, proveedor, prompt, sistema="", modelo_idx=0):
        self.recargar_configuracion_modelos()
        proveedor = proveedor.lower()
        self.last_usage = None

        if proveedor == "ollama":
            modelo = os.environ.get("DISBOARD_OLLAMA_MODEL", "").strip()
            if not modelo:
                return "[Error: Configure DISBOARD_OLLAMA_MODEL con un modelo instalado localmente]"
            base_url = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")
            parsed_url = urlparse(base_url)
            if parsed_url.scheme != "http" or parsed_url.hostname not in {"localhost", "127.0.0.1", "::1"}:
                return "[Error: El modo privado solo admite Ollama en localhost]"
            messages = []
            if sistema:
                messages.append({"role": "system", "content": sistema})
            messages.append({"role": "user", "content": prompt})
            try:
                response = requests.post(
                    f"{base_url}/api/chat",
                    json={"model": modelo, "messages": messages, "stream": False},
                    timeout=(5, 300),
                )
                response.raise_for_status()
                payload = response.json()
                self.last_usage = {
                    "input_tokens": payload.get("prompt_eval_count", 0),
                    "output_tokens": payload.get("eval_count", 0),
                    "source": "reported",
                }
                return payload["message"]["content"]
            except (requests.RequestException, KeyError, ValueError) as error:
                return f"[Error Ollama local]: {error}"

        # 1. GROQ INFERENCE (EX_MACHINA SPEED)
        if proveedor == "groq":
            if not HAS_GROQ:
                return "[Error: Librería 'groq' no instalada en Suniaster]"
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                return "[Error: GROQ_API_KEY no configurada en las variables de entorno]"
            
            pool = self.modelos_pool.get("groq", [])
            modelo = pool[modelo_idx]["modelo"] if modelo_idx < len(pool) else "openai/gpt-oss-20b"
            
            try:
                client = Groq(api_key=api_key)
                messages = []
                if sistema:
                    messages.append({"role": "system", "content": sistema})
                messages.append({"role": "user", "content": prompt})
                
                completion = client.chat.completions.create(
                    model=modelo,
                    messages=messages,
                    temperature=0.3
                )
                usage = completion.usage
                if usage:
                    self.last_usage = {
                        "input_tokens": usage.prompt_tokens,
                        "output_tokens": usage.completion_tokens,
                        "source": "reported",
                    }
                return completion.choices[0].message.content
            except Exception as e:
                print(f"⚠️ [SORA OBERON]: Groq falló con '{modelo}'. Detalle: {e}. Conmutando a Gemini...")
                return f"[Error de Inferencia Groq]: {e}"

        # 2. GEMINI INFERENCE (FLUGEL CONTEXT)
        elif proveedor in ["google", "gemini"]:
            if not HAS_GEMINI:
                return "[Error: Librería 'google-genai' no instalada en Suniaster]"
            api_key = os.environ.get("GOOGLE_AI_STUDIO_API_KEY") or os.environ.get("GEMINI_API_KEY")
            if not api_key:
                return "[Error: GOOGLE_AI_STUDIO_API_KEY no configurada]"
            
            pool = self.modelos_pool.get("gemini", [])
            modelo = pool[modelo_idx]["modelo"] if modelo_idx < len(pool) else "gemini-2.5-flash"
            
            try:
                client = genai.Client(api_key=api_key)
                full_prompt = f"{sistema}\n\n{prompt}" if sistema else prompt
                response = client.models.generate_content(
                    model=modelo,
                    contents=full_prompt
                )
                usage = response.usage_metadata
                if usage:
                    self.last_usage = {
                        "input_tokens": usage.prompt_token_count or 0,
                        "output_tokens": usage.candidates_token_count or 0,
                        "source": "reported",
                    }
                return response.text
            except Exception as e:
                return f"[Error de Inferencia Gemini]: {str(e)}"

        # 3. CLAUDE INFERENCE (ELFEN LOGIC)
        elif proveedor in ["anthropic", "claude"]:
            print(f"🔔 [{COLOR_PRIMARY}ALERTA DE CUOTA GRATUITA{COLOR_RESET}]: Se invoca a Claude de Anthropic.")
            if not HAS_ANTHROPIC:
                return "[Error: Librería 'anthropic' no instalada]"
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                return "[Simulación Elfen]: Claude no tiene API Key configurada. Retornando simulación lógica de Shiro."

            pool = self.modelos_pool.get("anthropic", [])
            modelo = pool[modelo_idx]["modelo"] if modelo_idx < len(pool) else "claude-3-5-sonnet-20241022"
            try:
                client = anthropic.Anthropic(api_key=api_key)
                system_p = sistema if sistema else anthropic.NotGiven
                message = client.messages.create(
                    model=modelo,
                    max_tokens=2048,
                    system=system_p,
                    messages=[{"role": "user", "content": prompt}]
                )
                usage = message.usage
                if usage:
                    self.last_usage = {
                        "input_tokens": usage.input_tokens,
                        "output_tokens": usage.output_tokens,
                        "source": "reported",
                    }
                return message.content[0].text
            except Exception as e:
                return f"[Error Claude]: {e}"

        # 4. CHATGPT INFERENCE (DHAMPIR NARRATIVE)
        elif proveedor in ["openai", "chatgpt"]:
            print(f"🔔 [{COLOR_SECONDARY}ALERTA DE CUOTA GRATUITA{COLOR_RESET}]: Se invoca a ChatGPT de OpenAI.")
            if not HAS_OPENAI:
                return "[Error: Librería 'openai' no instalada]"
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                return "[Simulación Dhampir]: ChatGPT no tiene API Key configurada. Retornando simulación narrativa de Stephanie Dola."

            pool = self.modelos_pool.get("openai", [])
            modelo = pool[modelo_idx]["modelo"] if modelo_idx < len(pool) else "gpt-4o-mini"
            try:
                client = openai.OpenAI(api_key=api_key)
                messages = []
                if sistema:
                    messages.append({"role": "system", "content": sistema})
                messages.append({"role": "user", "content": prompt})
                response = client.chat.completions.create(
                    model=modelo,
                    messages=messages,
                    temperature=0.7
                )
                usage = response.usage
                if usage:
                    self.last_usage = {
                        "input_tokens": usage.prompt_tokens,
                        "output_tokens": usage.completion_tokens,
                        "source": "reported",
                    }
                return response.choices[0].message.content
            except Exception as e:
                return f"[Error OpenAI]: {e}"

        return f"[Error: Proveedor '{proveedor}' no soportado en Suniaster]"

    @staticmethod
    def _es_error_de_inferencia(respuesta):
        return respuesta.startswith("[Error") or respuesta.startswith("[Simulación")

    def consultar_ia(self, agente, prompt, requiere_pro=False, proveedor_preferido="", solo_local=False):
        agente_lower = agente.lower()
        rutas_agente = {}
        config_path = self.root_dir / "exeed_config.json"
        try:
            rutas_agente = json.loads(config_path.read_text(encoding="utf-8")).get("agent_models", {})
        except (OSError, json.JSONDecodeError):
            pass

        ruta_agente = {} if solo_local else rutas_agente.get(agente_lower, {})
        modelo_agente = ruta_agente.get("model")
        if solo_local:
            proveedor_preferido = "ollama"
            modelo_agente = os.environ.get("DISBOARD_OLLAMA_MODEL", "").strip()
            if not modelo_agente:
                return "[Error: Configure DISBOARD_OLLAMA_MODEL para usar el modelo local]", "ERROR_CONFIG"
            self.modelos_pool["ollama"] = [{"modelo": modelo_agente, "rol": "LOCAL"}]
        elif ruta_agente:
            proveedor_preferido = ruta_agente.get("provider", proveedor_preferido).lower()
        elif not proveedor_preferido:
            if any(a in agente_lower for a in ["jibril", "fiel"]):
                proveedor_preferido = "gemini"
            elif any(a in agente_lower for a in ["stephanie", "dola"]):
                proveedor_preferido = "openai"
            else:
                proveedor_preferido = "groq"
        
        prov_key = proveedor_preferido.lower()
        if prov_key not in self.modelos_pool:
            prov_key = "gemini"
        
        pool_prov = self.modelos_pool.get(prov_key, [])
        idx_modelo = next(
            (i for i, item in enumerate(pool_prov) if item.get("modelo") == modelo_agente),
            None,
        ) if modelo_agente else None
        if modelo_agente and idx_modelo is None:
            return f"[Error: El modelo configurado para {agente} no existe en el pool {prov_key}]", "ERROR_CONFIG"
        if idx_modelo is None:
            idx_modelo = 0 if requiere_pro else (1 if len(pool_prov) > 1 else 0)
        
        modelo_seleccionado = pool_prov[idx_modelo]["modelo"] if pool_prov else "default"
        tag_modelo = f"{prov_key}/{modelo_seleccionado}"
        print(f"🤖 [{agente.upper()}]: Procesando vía {prov_key.capitalize()} ({modelo_seleccionado})...")
        
        sistema_prompt = f"Eres {agente}, miembro del núcleo inteligente de Disboard-NGNL en Suniaster. Bajo la soberanía de Tet."
        proveedores = [prov_key] if solo_local else (
            [prov_key] + [p for p in ("groq", "gemini", "anthropic", "openai") if p != prov_key]
        )
        for proveedor in proveedores:
            pool = self.modelos_pool.get(proveedor, [])
            if not pool:
                continue
            indices = list(range(len(pool)))
            indices.sort(key=lambda indice: indice != idx_modelo)
            for indice in indices:
                respuesta = self._llamar_proveedor(proveedor, prompt, sistema_prompt, modelo_idx=indice)
                if not self._es_error_de_inferencia(respuesta):
                    modelo_usado = pool[indice]["modelo"]
                    etiqueta = tag_modelo if proveedor == prov_key and indice == idx_modelo else f"FALLBACK_{proveedor}/{modelo_usado}"
                    usage = self.last_usage or {
                        "input_tokens": estimate_tokens(sistema_prompt + prompt),
                        "output_tokens": estimate_tokens(respuesta),
                        "source": "estimated",
                    }
                    self.usage_ledger.record(
                        agente, proveedor, modelo_usado,
                        usage["input_tokens"], usage["output_tokens"], usage["source"],
                    )
                    return respuesta, etiqueta
        
        return respuesta, tag_modelo

    def registrar_en_bitacora_local(self, slug, agente, modelo_tag, tarea, estado, notas):
        """Registra la actividad quirúrgicamente en la bitácora Markdown del contrato local."""
        context_file = self.root_dir / slug / "contract.md"
        if not context_file.exists():
            return
        
        contenido = context_file.read_text(encoding="utf-8")
        fecha_actual = datetime.now().strftime("%d/%m/%Y")
        nueva_entrada = f"* {fecha_actual} - [{agente} / {modelo_tag}]: {tarea} | Estado: `{estado}` | Notas: {notas}\n"
        
        ancla = "## Historial y Bitácora (Orden Cronológico Inverso)"
        if ancla in contenido:
            partes = contenido.split(ancla)
            # Inyección limpia en orden cronológico inverso
            contenido_actualizado = partes[0] + ancla + "\n\n" + nueva_entrada + partes[1].replace("\n\n", "\n", 1)
            context_file.write_text(contenido_actualizado, encoding="utf-8")
        else:
            # Si no está la cabecera, la agregamos al final
            contenido_actualizado = contenido + f"\n\n## Historial y Bitácora (Orden Cronológico Inverso)\n\n{nueva_entrada}"
            context_file.write_text(contenido_actualizado, encoding="utf-8")
