# Guía de despliegue e integración en GitHub

> Documento operativo. Complementa al `README.md`, al `.env.example` y al
> `docs/manual.md`.

## 1. Crear el repositorio privado

1. En GitHub, crear un repositorio **privado** llamado `Disboard-NGNL`.
2. No inicializar con README, `.gitignore` ni licencia (ya existen en local).
3. Copiar la URL del repositorio.

## 2. Configurar secretos en Codespaces

En **Settings → Secrets and variables → Codespaces**, añadir:

| Secreto | Obligatorio | Uso |
|---|---|---|
| `GOOGLE_AI_STUDIO_API_KEY` | Sí (free tier) | Gemini / Antigravity de Shiro |
| `GROQ_API_KEY` | Sí (free tier) | Suniaster (proveedor por defecto) |
| `OPENAI_API_KEY` | No (pago) | Suniaster (solo si Tet autoriza) |
| `ANTHROPIC_API_KEY` | No (pago) | Suniaster (solo si Tet autoriza) |
| `DEEPSEEK_API_KEY` | No (pago) | Suniaster (solo si Tet autoriza) |
| `WOLFRAM_API_KEY` | Pendiente | Cálculos simbólicos de Shiro |
| `CROSSREF_MAILTO` | Sí | Jibril (polite pool de Crossref) |
| `OPENALEX_API_KEY` | Recomendado | Jibril (mayor cuota diaria) |
| `ORCID_TOKEN` | Opcional | Jibril (solo si se requiere lectura limitada) |
| `TET_SIGNING_KEY` | Sí | Firma HMAC de aprobaciones HITL de Tet |

> `TET_SIGNING_KEY` debe generarse con:
> `python -c "import secrets; print(secrets.token_hex(32))"`
> y **no** reutilizarse entre entornos.

## 3. Subir los archivos desde Codespaces

```bash
# 1. Verificar estado
git status

# 2. Añadir todo el contenido versionable
git add .

# 3. Forzar archivos que pudieran estar ignorados por reglas previas
git add --force .devcontainer/Dockerfile .devcontainer/devcontainer.json

# 4. Verificar qué se va a commitear (auditoría)
git status --short

# 5. Commit inicial
git commit -m "SUNI_BOOTSTRAP: Despliegue completo de Disboard-NGNL v1.0.0"

# 6. Push a main
git push origin main
