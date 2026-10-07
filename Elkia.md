# 🏰 Elkia: Registro Maestro y Seguimiento de Proyectos (Edge)
---
### Índice Maestro e Institucional de Disboard-NGNL
**Autoridad Soberana:** Tet 『 』
**Interfaz de Entrada & Consola HITL:** Terminal Suniaster / Consola Disboard (`disboard_console.py`)
**Núcleo Inteligente (Kuhaku):** Sora, Shiro, Stephanie Dola & subagentes
**Espacio Activo (Codespace):** Suniaster

---

## 🏛️ Directrices de Arquitectura y Gobernanza del Sistema
Los agentes del ecosistema multiagente 『 』 (Kuhaku: **Sora**, **Shiro**, **Stephanie Dola**, y sus subagentes **Jibril**, **Izuna Hatsuse**, **Kurami Zell**, **Clammy Zell**, **Fiel Nirvalen**) leerán primero el contexto operativo de este índice maestro. Solo después de identificar o crear un edge leerán su contrato local (`contract.md`) y las peticiones (`docs/peticiones_tet.md`). La lectura global se limita a gobernanza, roles, proyectos activos y convenciones para evitar cargar información irrelevante.

### ⚖️ Reglas de Operación (Resumen Operativo)
1. **Creación y Alta:** **Tet** tiene el derecho exclusivo de iniciar un edge. Escribe una petición libre para crear el proyecto; Sora solicita el ID y los datos de registro que falten, conserva la plantilla completa y lo agrega a este registro.
2. **Matriz inicial:** Antes de pedir una acción, la consola obtiene todos los proyectos de esta tabla y la fecha objetivo de sus contratos, y los presenta en cuatro cuadrantes con colores. Fiel Nirvalen prepara una matriz independiente desde `AGENDAS_Y_CURSOS.md`.
3. **Entrada libre y enrutamiento:** Sora interpreta cada petición libre y la dirige a un proyecto registrado, creación de edge, correo, informe, agenda, bibliografía u otro asunto. Si no puede identificar un único destino, solicita aclaración o el ID; no escoge un proyecto al azar.
4. **Atención de peticiones:** Cuando la solicitud corresponde a un proyecto, se registra en `docs/peticiones_tet.md` y el especialista la atiende en el mismo ciclo. El registro es trazabilidad, no sustituto del trabajo. La solicitud y cualquier contexto privado se envían a proveedores externos solo con consentimiento de Tet; sin él se usa Ollama local.
5. **Contextualización Contractual:** El agente consulta este registro global y después el contrato local `contract.md`, las peticiones y los insumos expresamente autorizados. Los cambios de alcance se presentan como candidatos basados en `contract-template.md`; **Tet** debe aprobarlos antes de actualizar el contrato activo.
6. **Restricción de Iniciativa Autónoma:** Ningún agente o subagente publicará en la rama principal de GitHub (`main`), enviará correos, aprobará referencias ni confirmará cambios de agenda/contrato sin una instrucción directa o veredicto de **Tet**.
7. **Soberanía y Veredicto (HITL):** Todo cambio de estado de un entregable o proyecto al estado de `COMPLETO` requiere la aprobación formal y el veredicto explícito de **Tet** (Aprobar, Modificar o Aplicar Rollback). Sora puede sugerir avances y siguientes acciones basados en evidencia, pero se registran en Elkia.md únicamente después de una aprobación explícita e independiente de Tet; las fechas objetivo cambian al aprobar una propuesta contractual.
8. **Auditoría e Informes:** Los agentes cooperan para generar informes. La diplomática **Stephanie Dola** y su subagente **Fiel Nirvalen** auditan las bitácoras y proponen reportes, pero carecen de autoridad para aprobarlos o modificar contratos sin el veredicto de **Tet**.

## 🧩 Arquitectura de Skills de Kuhaku
La analogía de No Game No Life se conserva como modelo operativo: **Elkia** es el tablero, cada `edge-*` es un territorio, **Tet** dicta la jugada, **Sora** la descompone y **Kuhaku** ejecuta mediante capacidades especializadas.

Las capacidades reutilizables se describen en `skills/<nombre>/SKILL.md`. La consola y LangGraph cargan primero este índice global; una vez elegido un edge, consultan `contract.md` y las peticiones operativas de `docs/peticiones_tet.md`. Los contratos no deben copiar las reglas, roles ni capacidades globales que ya se describen aquí.

| Capa | Ubicación | Función de seguimiento |
| :--- | :--- | :--- |
| Tablero soberano | `Elkia.md` | Registro de territorios, estado global y autoridad HITL. |
| Matriz de proyectos | `Elkia.md` + fecha en `<edge>/contract.md` | Cuatro cuadrantes locales; Q1 rojo, Q2 amarillo, Q3 azul, Q4 gris. † marca ejes con datos faltantes. |
| Matriz de agenda | `AGENDAS_Y_CURSOS.md` | Pendientes generales de Tet administrados por Fiel Nirvalen y confirmados por Tet. |
| Alcance contractual | `<edge>/contract.md` | Objetivos, metas, entregables y cronograma aprobados. |
| Peticiones dinámicas | `<edge>/docs/peticiones_tet.md` | Entrada libre registrada y atendida por el especialista; los cambios contractuales requieren aprobación de Tet. |
| Capacidades | `skills/` | Procedimientos reutilizables por agente, entradas, salidas y validaciones. |
| Evidencia | `<edge>/docs/` y `<edge>/src/` | Entregables revisables desde el explorador. |
| Evaluaciones | `evals/` | Comprobaciones del flujo de creación, ejecución, revisión y rollback. |

## 🏛️ Directrices de Ejecución para los Agentes
Los agentes operarán con lecturas quirúrgicas por secciones para reducir el consumo de tokens. Cada agente y subagente trabajará cuando tenga una tarea asignada que corresponda con su rol, registrando el resultado en el contrato o bitácora del proyecto correspondiente. Cada skill está asociada al agente de la misma fila; no repetir su procedimiento en los contratos.

| Agente | Rol y responsabilidades |
| :--- | :--- |
| **Sora** | Estrategia, desglose de tareas, cronograma y coordinación de validaciones. |
| **Shiro** | Código Python, cómputo simbólico, simulaciones y pruebas unitarias. |
| **Stephanie Dola** | Publicación, estilo, maquetado y revisión final de entregables. |
| **Fiel Nirvalen** | Agendas, auditoría de bitácoras y borradores de comunicación anonimizados. |
| **Izuna Hatsuse** | Recolección, limpieza, validación y paralelización de datos y APIs. |
| **Jibril** | Búsqueda bibliográfica, minería de metadatos y borradores científicos. Cada referencia propuesta debe verificarse en al menos una de Crossref, OpenAlex u ORCID mediante su DOI. |
| **Kurami Zell** | Crítica de consistencia teórica, física y lógica. |
| **Clammy Zell** | Verificación de alineación entre código, simulaciones y objetivos. |

### Registro de skills por agente y subagente

La consola y LangGraph cargan el archivo correspondiente a la tarea asignada. La skill
detalla el procedimiento del rol; este registro global indica dónde encontrarla.

| Agente / subagente | Skill reutilizable |
| :--- | :--- |
| Sora | `skills/planificacion-sora/SKILL.md` |
| Shiro | `skills/ejecucion-shiro/SKILL.md` |
| Stephanie Dola | `skills/revision-stephanie/SKILL.md` |
| Fiel Nirvalen | `skills/asistencia-fiel/SKILL.md` |
| Izuna Hatsuse | `skills/ingenieria-datos-izuna/SKILL.md` |
| Jibril | `skills/bibliografia-jibril/SKILL.md` |
| Kurami Zell | `skills/revision-critica-kurami/SKILL.md` |
| Clammy Zell | `skills/alineacion-clammy/SKILL.md` |

### Capacidades principales implementadas y límites actuales

El contrato de cada edge define el problema, los insumos, los criterios de aceptación y los productos particulares. Las funciones comunes residen en el sistema y se activan según la tarea:

| Función común | Comportamiento del sistema | Participación de IA / control |
| :--- | :--- | :--- |
| Matrices y prioridades | La consola obtiene registros de proyecto de Elkia, fechas de sus contratos y tareas de agenda de Fiel; clasifica sin inferencia de IA y recomienda el cuadrante activo más urgente. | Fechas/avance explícitos; datos faltantes se marcan como prioridad provisional. |
| Entrada libre y enrutamiento | Sora dirige una petición a proyecto, creación, correo, informe, agenda, bibliografía u otra respuesta; pide ID/aclaración cuando no hay un destino claro. | IA para clasificar y producir; las operaciones con efectos persistentes requieren confirmación de Tet. |
| Planificación y producción | Las solicitudes de proyecto se registran y ejecutan en el mismo ciclo; los borradores/artefactos se presentan para HITL. Contratos candidatos preservan el contrato vigente hasta aprobación. | Agentes y proveedores configurados; consentimiento explícito antes de enviar contexto a proveedores externos. |
| Grafo web LangGraph | Ejecuta Sora → Jibril opcional (si hay notas bibliográficas) → Shiro → Kurami, con hasta una corrección; devuelve borrador y crítica sin escribir entregables. | Ollama local; aprobación humana necesaria. SQLite guarda checkpoints, no datos analíticos. |
| Revisión externa | Sora evalúa observaciones, Kurami audita y un agente prepara respuesta y copia candidata; no sobrescribe el original. | Ollama local; Tet decide si integra los cambios. |
| PDF y bibliografía | Extracción textual PDF→Markdown sin IA conserva el PDF original y marca páginas sin texto; una búsqueda DOI en OpenAlex puede proponer trabajos citantes. | Jibril puede cribar localmente; solo Tet aprueba nuevas referencias. La extracción no preserva fielmente gráficos, tablas visuales ni OCR. |
| Tabulares y bases estandarizadas | El módulo `edge-bases_de_datos` importa CSV/JSON/Excel según esquema explícito, valida tipos/columnas/claves y genera reporte de auditoría local. | Determinista, no requiere IA para transformar datos. |
| Informes y preprints desde manifiesto | `disboard_reports.py` ensambla Markdown/LaTeX desde contenido y datos proporcionados; el estilo tiene herramientas separadas. | La composición por plantilla es local y determinista; la redacción contextual puede requerir IA y revisión de Tet. |
| Archivos locales y relay | La web guarda/lista/descarga artefactos privados con hash. `disboard_relay.py` transfiere artefactos manualmente sobre HTTPS; no ejecuta agentes remotos ni integra automáticamente en el edge. | Configuración y secreto de relay a cargo del operador; SHA-256 detecta alteraciones, no cifra datos en reposo. |
| Plugins | Contrato de plugin v1 y allowlist explícita; el almacenamiento local es el primer bloque conectado. | Importar un plugin ejecuta código de confianza; los demás bloques aún no están conectados al registro. |

**Límites de despliegue:** el backend guarda en el equipo donde se ejecuta. Codespaces sigue siendo remoto aunque se use relay; VPN/TLS protegen el canal, no vuelven local el cómputo ni eliminan copias cloud. La suite Windows/Linux y los flujos de agente en cada proveedor requieren pruebas del ambiente concreto.

## 🛠️ Pool de Herramientas, Modelos y Cómputo
El pool global disponible para los proyectos incluye:

- **Software y cómputo:** GitHub, GitHub Codespaces, VS Code, Anaconda Python 3.12, SymPy, Pandas, NumPy, Matplotlib, LaTeX, Wolfram Language, Jupyter y Git.
- **APIs científicas:** OpenAlex, Crossref y ORCID, según sus límites y condiciones de uso. Una propuesta bibliográfica de Jibril es válida cuando cada DOI aparece al menos en una de estas fuentes.
- **Modelos de IA:** Groq Engine, Google AI Studio, Anthropic Claude y OpenAI ChatGPT, seleccionados según la tarea, disponibilidad y límites operativos.
- **Configuración específica:** Cada contrato solo debe declarar herramientas, modelos o dependencias adicionales que sean particulares de su proyecto.

## ⚖️ Delegación y Matriz de Autorizaciones
Todos los agentes y subagentes están **AUTORIZADOS** por defecto para ejecutar tareas asignadas a su rol. La asignación de una tarea define el alcance operativo; Tet conserva la validación final de estados, entregables y cambios soberanos.

| Agente / Recurso | Alcance autorizado | Condición de ejecución |
| :--- | :--- | :--- |
| **Sora** | Contexto, estrategia y cronogramas | Tarea asignada a su rol |
| **Shiro** | Código, simulaciones y pruebas | Tarea asignada a su rol |
| **Stephanie Dola** | Edición, estilo y publicación | Tarea asignada a su rol |
| **Fiel Nirvalen** | Administración y auditoría | Tarea asignada a su rol |
| **Izuna Hatsuse** | Datos y APIs | Tarea asignada a su rol |
| **Jibril** | Fuentes y bibliografía | Tarea asignada a su rol |
| **Kurami Zell** | Crítica teórica y lógica | Tarea asignada a su rol |
| **Clammy Zell** | Alineación de metas | Tarea asignada a su rol |

La autorización operativa no sustituye el veredicto HITL de Tet ni permite publicar directamente en `main`, crear recursos remotos o marcar un entregable como `COMPLETO` sin la validación correspondiente.

---

## 📚 Registro Central de Territorios y Provenance
Este bloque es la fuente operativa de seguimiento. Cada proyecto se identifica por un ID único y una carpeta `edge-*`; el mismo ID conecta su estado, contrato, peticiones y trazabilidad de datos.

### 📊 Registro Maestro de Proyectos
<!-- REGISTRO_PROYECTOS_INICIO -->
| ID del Proyecto | Carpeta Edge | Título y Enfoque | Estado | Avance Global (%) | Último hito / movimiento | Siguiente acción | Última actualización | Responsable | Contrato | Peticiones |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **DOIS** | `edge-dataframe_dois_mineria` | Minería de DOIs a partir de ORCID ID | EN_PROCESO | 10% | Sin actualización verificada en este esquema | Tet/Sora: revisar contrato y registrar próximo hito | 2026-09-03 | Tet | `contract.md` | `docs/peticiones_tet.md` |
| **DF** | `edge-bases_de_datos` | Bases de Datos Normalizadas | EN_PROCESO | 10% | Tet abrió el edge para continuar el trabajo | Revisar el contrato y registrar el siguiente hito verificable | 2026-10-05 | Tet | `contract.md` | `docs/peticiones_tet.md` |
| **PTE** | `edge-plan_de_trabajo_especializado` | Análisis de redes de colaboración científica e impacto de proyectos SECIHTI/DICBF | NUEVO | 0% | Sin actualización verificada en este esquema | Tet/Sora: revisar contrato y registrar próximo hito | 2026-09-07 | Sora | `contract.md` | `docs/peticiones_tet.md` |
| **GRAPHOS** | `edge-redes_cientificas_graphos` | Analísis de redes de colaboración científica, mediante matrices de grafos | EN_PROCESO | 0% | Tet registró una petición o comentario | Incorporar la petición en el siguiente ciclo autorizado | 2026-10-05 | Sora | `contract.md` | `docs/peticiones_tet.md` |<!-- REGISTRO_PROYECTOS_FIN -->

> 💡 **Regla de actualización:** Este es el índice operativo leído antes de elegir un edge. Al crear, reanudar, aprobar o solicitar cambios, la consola actualiza el estado, el último movimiento y la fecha; Tet conserva el veredicto final para cambiar estados a `COMPLETO`. El porcentaje es una estimación de avance y no se incrementa sin evidencia contractual verificable.

### 📝 Bitácora de Provenance Global (Data Tracking)
*Para todos los proyectos que involucren descargas masivas de metadatos, búsquedas bibliográficas automatizadas o manipulación de archivos tabulares, se registrará cada transacción de manera obligatoria aquí. Las altas de proyectos también se registran como eventos `ALTA_PROYECTO`:*

<!-- PROVENANCE_INICIO -->
| ID Proyecto | API Origen | Tipo de Registro | Recuperado Por | Fecha / Hora | DOI / Identificador | Estado | Notas / Observaciones |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **NGNL** | Local | Configuración | Sora | 02/09/2026 14:00 | N/A | CORRECTO | Configuración limpia de 34 archivos de Repositorio Disboard-NGNL |
| **NGNL** | Elkia.md | BAJA_REGISTRO_ACTIVO | Tet | 2026-10-05 | N/A | REGISTRADO | Retirado del registro operativo por solicitud de Tet; se conserva esta traza histórica y no se borra automáticamente la carpeta física |
| **DOIS** | `edge-dataframe_dois_mineria` | ALTA_PROYECTO | Sora | 03/09/2026 | N/A | CORRECTO | Proyecto registrado en el tablero central |
| **DF** | `edge-bases_de_datos` | ALTA_PROYECTO | Sora | 03/09/2026 | N/A | CORRECTO | Proyecto registrado en el tablero central |
| **PTE** | `edge-plan_de_trabajo_especializado` | ALTA_PROYECTO | Sora | 07/09/2026 | N/A | CORRECTO | Proyecto registrado en el tablero central |
| **GRAPHOS** | `edge-redes_cientificas_graphos` | ALTA_PROYECTO | Sora | 05/10/2026 | N/A | CORRECTO | Proyecto registrado en el tablero central |
<!-- PROVENANCE_FIN -->

---

## ⚙️ Catálogo de Recursos, Motores y APIs Disponibles
*Este catálogo es la referencia estática oficial que los agentes consultarán para realizar búsquedas bibliográficas, modelados y llamadas de código en el entorno Suniaster.*

| Recurso / API | Proveedor / Licencia | Categoría | Propósito Principal en Disboard-NGNL | Autenticación y Límites | Referencia y Documentación |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OpenAlex** | OurResearch (Libre) | Scholarly Index | Mapa global del sistema de investigación científica. | API Pública Libre (Sin llave, hasta 100k consultas diarias). | [openalex.org](https://openalex.org) |
| **Crossref** | Crossref (PIL) | Metadata Registry | Registro, validación y distribución de metadatos académicos y enlaces DOIs. | API REST pública gratuita (Se requiere header de cortesía para el pool rápido). | [crossref.org](https://www.crossref.org) |
| **ORCID Registry** | ORCID, Inc. | Researcher Registry | Identificador persistente internacional para eliminar la ambigüedad en autores. | API Pública Gratuita (Búsqueda y lectura de perfiles sin límite estricto de tasa). | [orcid.org](https://orcid.org) |
| **LangChain / LangGraph** | LangChain Inc. (MIT) | Agentic Framework | Orquestación técnica de redes multiagente complejas con estado, memoria y ciclos. | Librería local. Conexión opcional a LangSmith para depuración profunda. | [docs.langchain.com](https://docs.langchain.com) |
| **Google AI Studio** | Google | Generative AI | **Familia Pro:** Razonamiento abstracto complejo.<br>**Familia Flash:** Síntesis masiva y procesamiento de bajo consumo. | Requiere variable de entorno `GOOGLE_AI_STUDIO_API_KEY`. | [ai.google.dev](https://ai.google.dev) |
| **Groq Engine** | Groq Inc. | Generative AI | Inferencia de ultra-alta velocidad para lógica de código (scripts en Python) y cálculos matemáticos (Llama-3-70B). | Requiere variable de entorno `GROQ_API_KEY`. | [groq.com](https://groq.com) |
| **Anaconda Platform** | Anaconda | Python & Data Science | Creación de entornos virtuales reproducibles, empaquetado de librerías y cómputo científico. | Licencia individual gratuita para desarrollo académico y prototipos locales. | [anaconda.com](https://www.anaconda.com) |
| **Wolfram Engine** | Wolfram | Technical Computing | Computación simbólica avanzada, álgebra computacional y validación de constantes físicas. | Gratuito para desarrolladores (Prototipado rápido y uso mediante API de Wolfram Cloud). | [wolfram.com/engine](https://www.wolfram.com/engine) |

---

## 🗂️ Convenciones de Estado de Proyectos
- **NUEVO:** Proyecto registrado en Elkia; contrato pendiente de revisión y aprobación.
- **EN_PROCESO:** Se están ejecutando tareas contractuales o atendiendo observaciones.
- **EN_REVISION:** La evidencia contractual indica que los entregables están preparados; Tet debe revisar el paquete.
- **BLOQUEADO:** Hay una dependencia, decisión o insumo pendiente que impide avanzar; registrar la causa y responsable.
- **PAUSADO:** Tet decidió suspender temporalmente el trabajo.
- **COMPLETO:** Proyecto formalmente aprobado por Tet. La aprobación no publica ni sincroniza archivos por sí sola.

El porcentaje debe derivarse de hitos definidos en el contrato y evidencia registrada; si no es posible calcularlo, mantener el valor anterior y describir la limitación en el último movimiento.

---

## 📦 Convenciones de Formato de Resultados
Los entregables de cada proyecto activo deben generarse exclusivamente bajo las siguientes extensiones estandarizadas según su naturaleza:
* **Documentación y Reportes:** `.md` (Markdown), `.pdf` (Portable Document Format), `.docx` (Word editable).
* **Cómputo y Código:** `.py` (Scripts de Python), `.ipynb` (Jupyter Notebooks) o `.wl` / `.nb` (Wolfram Notebooks).
* **Bases de Datos:** `.csv` (Valores separados por comas), `.xlsx` (Libro de Excel).
* **Preprints y Ciencia:** `.tex` (Fuentes LaTeX compiladas a PDF bajo normas APA/IEEE).
* **Presentaciones:** Beamer en `.tex` (compilado a PDF) o diapositivas autogeneradas `.pptx`.
---
