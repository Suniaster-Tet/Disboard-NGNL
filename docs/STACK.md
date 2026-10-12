# Stack técnico

Este documento distingue dependencias declaradas, componentes usados y decisiones pendientes. La lista instalable está en `requirements.txt`; las dependencias opcionales del navegador están en `requirements-browser.txt`.

## Librerías por capa

| Capa | Librerías y herramientas | Estado y responsabilidad |
|---|---|---|
| Runtime | Python 3.12 | Versión usada como referencia de desarrollo; la compatibilidad por plataforma sigue sujeta a CI. |
| Web/API | FastAPI, Uvicorn, Pydantic, python-multipart | FastAPI/Uvicorn sirven la interfaz. Pydantic valida solicitudes HTTP (`LoginRequest`, `RunRequest`, `DOIRequest`); se declara directamente porque el código lo importa directamente. |
| Agentes | LangGraph, LangChain Core, `langgraph-checkpoint-sqlite` | Orquestación y checkpoints de la interfaz web. Los SDK de Groq, Google GenAI, Anthropic y OpenAI habilitan proveedores de consola según configuración y consentimiento. |
| HTTP y bibliografía | `requests` síncrono | Crossref, OpenAlex y ORCID verifican DOI en consola solo con el opt-in `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1`. La web usa la misma autorización para metadatos Crossref/OpenAlex y enriquecimiento DOAJ v3; DOAJ puede devolver presencia en el índice, revista e ISSN. No sustituye la verificación DOI ni evalúa calidad científica. |
| Persistencia operativa | `sqlite3` de la biblioteca estándar; SQLite de LangGraph; sistema de archivos | Registros de acceso/uso, checkpoints y artefactos locales. Los checkpoints no son el almacén analítico de los edges. |
| Datos tabulares | Pandas, Polars, NumPy, Dask, OpenPyXL, NumPy Financial | Pandas y Polars ya están declarados en `requirements.txt`. Pandas aparece en pruebas de Excel; no se observa todavía un flujo de producción que integre ambos motores. Se deben elegir por tarea y validar con datos representativos, no convertir todo entre ellos sin necesidad. |
| Ciencia y simulación | SymPy, SciPy, SimPy; PyTorch, Transformers, Accelerate | Cálculo simbólico, científico, simulación y modelos locales opcionales. No son requisitos de cada ruta de ejecución. |
| Documentos | python-docx, python-pptx, ReportLab, Jinja2, pypdf | Extracción PDF y generación/ensamblado de documentos. |
| Interfaz de consola | Rich | Presentación de la consola HITL. |

## Decisiones de almacenamiento y despliegue

- **SQLite es la opción adecuada hoy** para sesiones, checkpoints y registros locales: no requiere servidor y coincide con el patrón de uso actual. Mantén bases distintas por responsabilidad; no conviertas los checkpoints de LangGraph en catálogo científico compartido.
- **DuckDB no reemplaza SQLite.** Conviene evaluarlo si aparecen consultas analíticas grandes, agregaciones/joins columnares o conjuntos que ya no caben eficientemente en el proceso actual. Antes de adoptarlo, compara una carga real y define formato, migración y concurrencia.
- **Podman es un runtime de contenedores, no una base de datos.** No se requiere para el modo local actual ni resuelve almacenamiento, sincronización o privacidad. Puede evaluarse para desplegar servicios aislados/rootless; el repositorio ya contiene configuración Dev Container basada en Docker y cualquier sustitución debe probar compatibilidad.
- **Pandas y Polars son motores alternativos/complementarios de procesamiento.** Pandas favorece compatibilidad amplia y análisis en memoria; Polars ofrece ejecución columnar/lazy y opciones de streaming. Selecciona uno por etapa según tamaño, memoria, formatos y dependencias; conserva SQLite cuando se necesita persistencia relacional transaccional.

## APIs bibliográficas

La documentación de DOAJ está actualmente en [API documentation](https://doaj.org/api/docs); el enlace solicitado `/api/doc` responde 404. La consulta v3 por DOI devolvió resultados en la comprobación de integración. El conector reutiliza `requests` y solo consulta cuando `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1`; envía el DOI a un servicio público y registra el resultado como metadato, no como aprobación de la referencia.

El [Portal ISSN](https://portal.issn.org/) permite consultar registros en su sitio web, pero no se ha confirmado aquí un endpoint público de API, su autenticación, licencia ni límites. Por ello no se hace scraping ni se añade un cliente hasta disponer de esa especificación y credenciales/permiso aplicables. DOAJ ya puede proporcionar ISSN cuando su registro de artículo incluye ese dato.

No se incorpora `httpx`, `httpx.AsyncClient` ni `aiohttp`: los conectores bibliográficos actuales son síncronos y se invocan desde rutas síncronas. Si una futura operación asíncrona real lo requiere, se medirá latencia/concurrencia y se elegirá un solo cliente; no se mantendrán dos pilas HTTP en paralelo sin beneficio demostrado.
