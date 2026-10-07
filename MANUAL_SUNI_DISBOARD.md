# 📘 Manual de Operación de Codespace Suniaster y Tablero Disboard-NGNL
---
Este manual describe el tablero de entrada libre de **Suniaster**. Los únicos comandos de terminal necesarios son iniciar el programa y salir; las tareas se expresan en lenguaje natural.

---

## 🏛️ 1. Matriz y enrutamiento de peticiones

Ejecuta `python3 disboard_console.py`. Al comienzo se muestran dos matrices alimentadas por:

1. **Proyectos:** filas activas de `Elkia.md`, con fecha objetivo de `contract.md`, avance y siguiente acción del registro.
2. **Agenda general:** eventos de `AGENDAS_Y_CURSOS.md`, administrados por Fiel Nirvalen.

Los cuadrantes usan colores: Q1 rojo, Q2 amarillo, Q3 azul y Q4 gris. La urgencia se deriva de una fecha objetivo dentro de 7 días o vencida; la importancia, de avance inferior a 50%. Si falta la fecha, se considera no urgente; si falta el avance, importante provisionalmente y se marca `†`. Los proyectos cerrados y los eventos terminados se muestran aparte. Sora y Fiel sugieren el primer pendiente Q1, o el cuadrante activo más alto disponible.

En la entrada principal describe directamente el resultado que necesitas. Sora usa IA para identificar el destino:

* Un ID o tema de proyecto: la petición se agrega a `docs/peticiones_tet.md` y el agente pertinente produce un borrador/artefacto; si no hay entregables contractuales, prepara una respuesta directa revisable.
* Crear un proyecto: propone nombre y título, Tet confirma el ID y la idea inicial, y Sora crea el edge desde la plantilla sin podar módulos.
* Correo o informe: Fiel prepara el borrador solicitado. El correo no se envía automáticamente.
* Correo recibido: el router no ve el mensaje original; Fiel lo limpia localmente, muestra la vista previa y requiere confirmación de Tet. La respuesta queda dirigida a un destinatario general. Las respuestas aprobadas se guardan en una guía privada fuera de Git.
* Guía de respuestas: `guia-correo` permite importar un Markdown anonimizado de hasta 12 KB o registrar una respuesta general a mano; `subir-guia-correo "<ruta.md>"` importa directamente un archivo local.
* Agenda: Fiel consulta la matriz, propone un alta o cambio y Tet confirma antes de escribirlo.
* Bibliografía: Jibril/las herramientas locales extraen un PDF indicado; las referencias propuestas esperan la aprobación de Tet por DOI.
* Petición general: Sora responde o pide aclaración si no puede identificar un destino seguro.

Antes de usar IA se solicita permiso para enviar el contexto mínimo a un proveedor externo. Sin permiso, el sistema usa solo Ollama local. Las notas bibliográficas y los aportes privados tienen consentimiento separado.

El saneamiento de correo es local e incluye detección de correos electrónicos, teléfonos, enlaces y campos de encabezado de contacto. Tet debe revisar la vista previa, especialmente nombres, instituciones y detalles identificables que no se puedan detectar automáticamente. Si la vista previa no está suficientemente anonimizada, no la confirme ni continúe.

## 🛡️ 2. Contratos y aprobación HITL

Los módulos A–D son solo contenido de referencia dentro de la plantilla; se reemplazan por temas libres y combinables. Los cambios contractuales se guardan primero como propuesta en `docs/propuestas_contractuales/`; la versión actual permanece hasta que Tet apruebe la candidata. Cada borrador de trabajo también pasa por veredicto: aprobar, solicitar modificaciones o rechazar. Ningún agente cambia el estado del proyecto a `COMPLETO` por su cuenta.

Después de aprobar un artefacto, Sora puede sugerir el avance global y la siguiente acción a partir de la evidencia. Tet confirma esa propuesta en una aprobación aparte; solo entonces se actualiza `Elkia.md` y la matriz. Si Tet la rechaza, se conserva el registro vigente. Las fechas objetivo se actualizan al aprobar un contrato candidato.

Los resultados numéricos deben incluir método y unidades; el código, pruebas o pasos reproducibles; la literatura nueva, DOI verificado y estado pendiente de aprobación. La IA no garantiza corrección ni ejecución de comandos externos.

---

## 📑 3. Protocolo Wolfram Language (Tet Evaluation)

Para tareas que requieran el uso de **Wolfram Language**:
1. El agente de cálculo (**Shiro**) generará el código simbólico analítico basándose en las restricciones de Kurami Zell.
2. Shiro preparará un archivo de código para revisión HITL.
3. El archivo se guardará dentro de `edge-proyecto/src/`.
4. **Tus responsabilidades de juego:**
   - Toma el código entregado por Shiro y cópialo en tu interfaz de **Wolfram Cloud** o **Wolfram Engine** local para ejecutar la simulación.
   - Evalúa los gráficos o resultados de la corrida matemática.
   - Si detectas desvíos, describe la corrección en una nueva petición libre.
   - Si cumple los criterios, aprueba el artefacto y registra el hito.

---

## 🧬 4. Control de Sesión y Recuperación de Hitos (Git)

Puedes aprovechar el potencial de Git en Suniaster como puntos de restauración de tus proyectos científicos. Si necesitas retomar el desarrollo desde una versión o hito anterior:

```bash
# 1. Visualizar tu historial de jugadas registradas (commits)
git log --oneline

# 2. Restaurar un archivo específico de un proyecto al estado de un commit anterior
git checkout [HASH_DEL_COMMIT] -- edge-boseeinstein/src/app_base_shiro.py

# 3. Descartar de golpe todos los cambios actuales no guardados para reiniciar la sesión limpia
git checkout .

# 4. Revertir todo tu repositorio al estado completo de un hito anterior estable (Reset)
git reset --hard [HASH_DEL_COMMIT]
```
