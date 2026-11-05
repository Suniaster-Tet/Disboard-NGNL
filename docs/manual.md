# Manual de instalación y uso — Disboard-NGNL

> Guía completa para instalar, operar y acceder al ecosistema multiagente desde el equipo núcleo y desde clientes remotos (tablet, laptop secundaria) con garantías de ciberseguridad.
> Complementa al `README.md` (arquitectura y agentes).

---

## 1. Visión general del despliegue

Disboard-NGNL sigue un modelo **local-first**: el equipo núcleo ejecuta el backend, los agentes, las bases de datos y los artefactos. Los clientes (tablet, laptop secundaria, navegador) **solo consumen** la interfaz web o la terminal, sin almacenar datos sensibles.

```text
┌─────────────────────┐         ┌─────────────────────┐
│   Equipo núcleo     │         │   Cliente remoto    │
│  (laptop/PC/servidor)│◄───────►│  (tablet/laptop)    │
│                     │  HTTPS  │                     │
│  - Backend FastAPI  │  o SSH  │  - Navegador web    │
│  - Agentes          │         │  - Terminal SSH     │
│  - Base tensorial   │         │  - Jupyter (opcional)│
│  - Artefactos       │         │                     │
└─────────────────────┘         └─────────────────────┘
```
---
## 2. Requisitos del equipo núcleo

El equipo núcleo es donde reside todo el sistema. No necesita GPU si los modelos de IA se consumen vía API (que es el caso por defecto con Groq y Google AI Studio free tier).

### 2.1 Hardware mínimo y recomendado

| Componente | Mínimo | Recomendado |
|---|---|---|
| **CPU** | 2 vCPU | 4 vCPU o más |
| **RAM** | 4 GB | 8–16 GB |
| **Disco** | 20 GB libres | 50 GB SSD |
| **GPU** | No necesaria (API externa) | No necesaria; opcional para modelos locales |
| **Red** | Conexión estable a internet | Banda ancha con baja latencia |

> Si en el futuro ejecutas modelos locales con Ollama (por ejemplo, para Izuna), necesitarás VRAM adicional: ~8 GB para modelos 7–8B cuantizados. Para el flujo actual con APIs, 8–16 GB de RAM son suficientes.

### 2.2 Sistema operativo

- **Linux** (Ubuntu 22.04+, Debian 12+): recomendado.
- **macOS 13+** (Intel o Apple Silicon): compatible.
- **Windows 10/11** con WSL2: compatible.

### 2.3 Software requerido

| Software | Versión | Notas |
|---|---|---|
| Python | 3.11+ | El devcontainer usa 3.12 |
| Git | 2.40+ | Para clonar el repositorio |
| Docker + Docker Compose | 24+ | Solo si prefieres ejecutar los servicios en contenedores |
| LaTeX (TeX Live) | 2024+ | Solo si generas preprints; el devcontainer lo incluye |
| LibreOffice | 7.6+ | Solo si generas documentos Word; el devcontainer lo incluye |

> **Atajo:** si usas GitHub Codespaces, el devcontainer instala todo automáticamente. No necesitas instalar nada localmente.

### 2.4 Conectividad y puertos

| Puerto | Uso | Exposición |
|---|---|---|
| 8000 | Servidor web FastAPI | Solo localhost por defecto |
| 22 | SSH (si accedes al Codespace o al núcleo vía SSH) | Según configuración |

---
## 3. Requisitos de los equipos cliente

Los clientes **no ejecutan código ni almacenan datos**. Solo necesitan un navegador o una terminal SSH.

### 3.1 Tablet (iPad, Android) o laptop secundaria

| Requisito | Detalle |
|---|---|
| **Navegador moderno** | Chrome, Safari, Firefox, Edge (versiones recientes) |
| **Conexión a internet** | Para acceder vía túnel o VPN |
| **App SSH (opcional)** | Termius, Blink Shell (iPad), JuiceSSH (Android) si prefieres terminal |
| **Almacenamiento** | Mínimo; no se guardan datos locales |

### 3.2 Teléfono (opcional)

- Navegador móvil para consultar el dashboard.
- App SSH para terminal de emergencia.

---

## 4. Instalación en el equipo núcleo

### 4.1 Opción A — GitHub Codespaces (recomendado para empezar)

1. Crea el repositorio privado `Disboard-NGNL` en GitHub.
2. Sube el código (ver `docs/github-deployment.md`).
3. Configura los secretos en **Settings → Secrets and variables → Codespaces**:
   - `GROQ_API_KEY` (free tier)
   - `GOOGLE_AI_STUDIO_API_KEY` (free tier)
   - `TET_SIGNING_KEY` (genera con `python -c "import secrets; print(secrets.token_hex(32))"`)
   - `CROSSREF_MAILTO` (tu correo institucional)
   - `OPENALEX_API_KEY` (opcional, recomendado)
4. Abre el Codespace. El devcontainer instalará Python, LaTeX, LibreOffice, Antigravity CLI y las dependencias.
5. Ejecuta:

```bash
make healthcheck
make console
```

### 4.2 Opción B — Instalación local (laptop/PC/servidor)

```bash
# 1. Clonar el repositorio
git clone https://github.com/<tu-usuario>/Disboard-NGNL.git
cd Disboard-NGNL

# 2. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# 3. Instalar dependencias
pip install --upgrade pip
pip install -e ".[dev]"

# 4. Configurar variables de entorno
cp .env.example .env
# Edita .env con tus claves

# 5. Verificar
make healthcheck
```

### 4.3 Opción C — Docker Compose

```bash
# 1. Preparar el entorno y construir la imagen
cp .env.example .env
docker compose build

# 2. Levantar servicios (devcontainer, web, postgres)
docker compose up -d

# 3. Verificar
docker compose exec devcontainer make healthcheck
```

---
## 5. Modos de uso

### 5.1 Consola (recomendado para trabajo diario)

```bash
make console
# o
disboard start --seed mi_idea.md
disboard status
disboard dashboard
disboard check-models
```

**Ventajas:** escribe archivos, permite rollback, HITL completo con firma HMAC.

### 5.2 Servidor web local (dashboard)

```bash
make web
# o
uvicorn web.server:app --host 127.0.0.1 --port 8000
```

Abre `http://127.0.0.1:8000` en el navegador. En la portada puedes enviar una solicitud libre y crear un edge o continuar uno existente. En su detalle puedes:

* Revisar, editar y aprobar el plan de Sora.
* Proporcionar DOIs o buscar referencias sugeridas por Jibril; aprobar cada referencia antes de incorporarla.
* Ejecutar los entregables implementados o adjuntar archivos propios.
* Aprobar, modificar o rechazar entregables; el rechazo elimina el archivo y deja registro de rollback.
* Revisar hashes, avance, contrato y bitácora, y firmar el cierre.

Las aprobaciones requieren configurar `TET_SIGNING_KEY` en `.env` o en los secretos del Codespace. Las búsquedas de Jibril necesitan conexión a Crossref.

Para generar borradores con modelos gratuitos, deja `DISBOARD_USE_LLM=true` y configura al menos `GROQ_API_KEY` o `GOOGLE_AI_STUDIO_API_KEY`. Suniaster mantiene `allow_paid: false` en `suniaster/config.yaml`; si no hay credencial, cuota o respuesta válida, usa un scaffold local explícitamente pendiente de revisión.

### 5.3 Jupyter / JupyterLab (local o Codespaces)

```bash
jupyter lab
# o
jupyter notebook
```

En Codespaces, el puerto 8888 se reenvía automáticamente. Puedes usar los agentes desde celdas:

```python
from core.edge import Edge
from agents.sora.agent import SoraStrategist

edge = Edge.crear_desde_semilla(None, titulo="Demo Jupyter")
sora = SoraStrategist(edge_id=edge.id)
plan = sora.plan_edge(edge.id, "Analizar datos")
print(plan)
```

### 5.4 Google Colab (cómputo en nube, sin datos sensibles)
> **Advertencia:** Colab envía el código y los datos de entrada a los servidores de Google. **No lo uses con datos sensibles**. Úsalo solo para prototipos, demostraciones o cómputo pesado con datos públicos.

```python
!git clone https://github.com/<tu-usuario>/Disboard-NGNL.git
%cd Disboard-NGNL
!pip install -e ".[dev]"

import os
os.environ["GROQ_API_KEY"] = "tu_clave"
os.environ["TET_SIGNING_KEY"] = "tu_clave"
```

**Limitaciones:** sin Docker, LaTeX ni LibreOffice. El checkpointer web usa SQLite local.

### 5.5 VS Code (escritorio o navegador)

- **VS Code Web en Codespaces:** abre el Codespace desde el navegador.
- **VS Code Desktop + extensión GitHub Codespaces:** conéctate al Codespace con la experiencia completa de VS Code.
- **VS Code Desktop local:** abre la carpeta del repositorio clonado localmente.

### 5.6 SSH al Codespace (terminal pura desde tablet)

```bash
# Instalar GitHub CLI (una vez)
# Luego, desde la tablet:
gh codespace ssh --repo <tu-usuario>/Disboard-NGNL
```

Esto te da una terminal en el Codespace desde cualquier dispositivo con SSH. Ideal para tablets con Termius o Blink Shell.

---
## 6. Acceso remoto seguro desde otros equipos

### 6.1 Desde la misma red local (LAN)

No expongas FastAPI directamente por HTTP en la LAN. Para otros equipos, usa un reverse proxy con TLS delante y habilita la autenticación de la aplicación:

```bash
DISBOARD_WEB_REQUIRE_AUTH=true
DISBOARD_WEB_AUTH_USERNAME=tet
DISBOARD_WEB_AUTH_PASSWORD=<secreto de al menos 12 caracteres>
DISBOARD_WEB_TRUST_PROXY_HEADERS=true  # solo detrás de un proxy confiable
DISBOARD_WEB_ALLOWED_ORIGINS=https://disboard.intranet.example
WEB_HOST=127.0.0.1
make web
```

El proxy termina TLS y reenvía `X-Forwarded-Proto: https`; la app valida ese encabezado solo cuando `DISBOARD_WEB_TRUST_PROXY_HEADERS=true`. No habilites esa opción si se puede acceder al servidor sin pasar por el proxy.

### 6.2 Desde fuera de la red (Cloudflare Tunnel)

Cloudflare Tunnel permite exponer el servidor local sin abrir puertos en el router y sin IP pública. Requiere una cuenta de Cloudflare (gratuita) y un dominio (puede ser uno gratuito o de bajo costo).

**Pasos:**

1. Instala `cloudflared` en el equipo núcleo:

```bash
# Linux (Debian/Ubuntu)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb
```

2. Autentica:

```bash
cloudflared tunnel login
```

3. Crea el túnel:

```bash
cloudflared tunnel create disboard-ngnl
```

4. Configura el enrutamiento (ejemplo config.yml):

```yaml
tunnel: <TUNNEL_ID>
credentials-file: /home/<usuario>/.cloudflared/<TUNNEL_ID>.json
ingress:
  - hostname: disboard.tudominio.com
    service: http://localhost:8000
  - service: http_status:404
```

5. Crea el registro DNS:

```bash
cloudflared tunnel route dns disboard-ngnl disboard.tudominio.com
```

6. Ejecuta el túnel:

```bash
cloudflared tunnel run disboard-ngnl
```

**Seguridad:** Cloudflare aporta TLS; configura **Cloudflare Access** como primera capa y usuario/contraseña de la aplicación como segunda. Como Cloudflare conecta al origen desde loopback, en ejecución directa establece `DISBOARD_WEB_REQUIRE_AUTH=true`, `DISBOARD_WEB_TRUST_PROXY_HEADERS=true`, `DISBOARD_WEB_AUTH_USERNAME` y una contraseña de al menos 12 caracteres en `.env`. `docker-compose.yml` ya fuerza autenticación para el servicio web.

### 6.3 Alternativa: Quick Tunnel (temporal, sin cuenta)

Para pruebas rápidas sin dominio:

```bash
cloudflared tunnel --url http://localhost:8000
```

Genera una URL temporal `https://<aleatorio>.trycloudflare.com`. **Solo para pruebas; no uses esto para datos reales**.

### 6.4 Alternativa: ngrok (capa gratuita limitada)
ngrok ofrece túneles temporales con URL aleatoria en su plan gratuito. Limitaciones: URL cambia cada sesión, túneles de ~2 horas, sin autenticación avanzada.

```bash
ngrok http 8000
```
**No recomendado para uso continuo**. Usa Cloudflare Tunnel para algo permanente.

---
## 7. Ciberseguridad

### 7.1 Principios

| Principio | Implementación |
|---|---|
| **Mínima exposición** | El servidor escucha en `127.0.0.1` por defecto. Solo expón el puerto cuando uses un túnel. |
| **TLS obligatorio** | El middleware rechaza conexiones remotas por HTTP. En LAN usa reverse proxy TLS; nunca expongas HTTP plano. |
| **Autenticación** | Basic Auth de la aplicación es obligatoria para clientes remotos; Cloudflare Access es una capa adicional. `TET_SIGNING_KEY` firma decisiones HITL, no autentica sesiones. |
| **Filtrado de datos** | La búsqueda libre de Jibril aplica `privacy/filters.py` antes de Crossref. No se afirma que todas las futuras integraciones estén filtradas automáticamente. |
| **Secretos fuera del código** | Usa `.env` local o Secrets de Codespaces. Nunca commitees `.env`. |
| **Actualizaciones** | Mantén dependencias y `cloudflared` actualizados. |

### 7.2 Checklist de seguridad antes de exponer

- [ ] `TET_SIGNING_KEY` generada y configurada (no la default).
- [ ] `DISBOARD_WEB_AUTH_USERNAME` y contraseña fuerte configurados en `.env`.
- [ ] `DISBOARD_WEB_TRUST_PROXY_HEADERS=true` solo si todo tráfico llega por un proxy confiable.
- [ ] `DISBOARD_WEB_CHECKPOINT_DB` apunta a almacenamiento persistente si despliegas en contenedores.
- [ ] Cloudflare Access configurado para restringir acceso por correo.
- [ ] Firewall del núcleo permite solo tráfico saliente a Cloudflare (puerto 7844).
- [ ] `.env` en `.gitignore`.
- [ ] `privacy/prompts_policy.md` revisada.
- [ ] Backups de `edges/` y `logs/` configurados.

### 7.3 Qué NO hacer

- No expongas el puerto 8000 directamente a internet sin TLS.
- No uses Quick Tunnel para datos reales.
- No subas `.env` al repositorio.
- No ejecutes agentes con datos sensibles en Colab.
- No compartas la URL del túnel públicamente.

---
## 8. Flujo de trabajo diario

### 8.1 Iniciar un proyecto

```bash
disboard start --seed semilla.md
# Revisar plan de Sora
# Aprobar (1), Modificar (2) o Rechazar (3)
```

### 8.2 Consultar estado

```bash
disboard status
disboard dashboard
```

### 8.3 Revisar entregables

* Consola: `edges/<edge-id>/artifacts/`
* Dashboard web: abrir el edge y consultar la sección de entregables.
* Bitácora: `edges/<edge-id>/log.jsonl`

### 8.4 Aprobar cierre

```bash
disboard work <edge-id>
disboard approve <edge-id> --paso final
disboard reject <edge-id> --paso final
```

La consola y el dashboard comparten `workflow.json`, `contract.md`, `artifacts/` y `log.jsonl`; puedes alternar entre ambos para un mismo edge.

### 8.5 Acceso desde tablet

1. Abre el navegador de la tablet.
2. Ve a `https://disboard.tudominio.com` o al hostname HTTPS del reverse proxy.
3. Autentícate en Cloudflare Access si está configurado y en el diálogo Basic Auth de Disboard.
4. Consulta el dashboard, revisa artefactos o aprueba HITL.

---
## 9. Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| `TET_SIGNING_KEY no configurada` | Falta variable | Añadir a `.env` o Secrets |
| `503: credenciales requeridas` | No hay usuario/contraseña remotos válidos | Configurar `DISBOARD_WEB_AUTH_USERNAME` y contraseña de 12+ caracteres |
| `426: se requiere HTTPS` | Petición remota llegó por HTTP | Usar TLS en reverse proxy y reenviar `X-Forwarded-Proto: https` |
| `Suniaster degradado` | Falta API key | `disboard check-models` indica cuál |
| `No se puede cargar el dashboard` | El servidor web no está activo | `make web` y revisar `logs/web_graph_checkpoints.sqlite` |
| `cloudflared: command not found` | No instalado | Instalar desde el `.deb` o binario |
| `Tunnel no conecta` | Firewall bloquea puerto 7844 | Permitir salida TCP/UDP 7844 |
| `Tablet no carga el dashboard` | IP incorrecta o firewall local | Verificar IP y que el servidor escuche en `0.0.0.0` |
| `Playwright: navegadores no instalados` | Faltan binarios | `python -m playwright install --with-deps` |
| `Wolfram: mock` | Falta `WOLFRAM_API_KEY` | Shiro declara incertidumbre; no inventa |

---

## 10. Referencias rápidas

| Documento | Contenido |
|---|---|
| `README.md` | Arquitectura, agentes, flujo |
| `docs/architecture.md` | Diagrama de arquitectura y componentes |
| `docs/agent_roles.md` | Roles y analogías NGNL |
| `docs/github-deployment.md` | Despliegue en Codespaces |
| `docs/web-local.md` | Endpoints del servidor web |
| `privacy/prompts_policy.md` | Política de prompts externos |
| `suniaster/config.yaml` | Modelos por agente |

---

✦ **¡Aschente!** ✦
