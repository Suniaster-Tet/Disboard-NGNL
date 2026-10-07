# Tablero Web Local de Disboard

La web es un cliente del equipo anfitrión; los proyectos, las sesiones, los checkpoints y los contadores viven en ese equipo. No hay alta pública ni sincronización automática a GitHub. «Local» significa local al equipo donde corre el proceso: **Codespaces es infraestructura remota**, no el disco físico del usuario.

Al iniciar la consola, el primer índice que se carga es `Elkia.md`; al elegir o crear un edge, se consulta después su `contract.md`. La lista web también procede del registro activo de Elkia, no de explorar cualquier carpeta `edge-*`. Estado, último movimiento, fecha y siguiente acción se actualizan al avanzar por decisiones HITL. Solo se recalcula el porcentaje cuando hay evidencia contractual suficiente.

## Preparar el laptop

1. Instala Python 3.12, Git y Ollama en el laptop. Descarga con Ollama un modelo que pueda ejecutar el hardware disponible.
2. Crea un entorno virtual e instala dependencias:

   ```sh
   python3 -m venv .venv
   . .venv/bin/activate
   python -m pip install -r requirements.txt
   ```

3. Selecciona el modelo local y, si quieres, una carpeta privada de datos fuera del repositorio:

   ```sh
   export DISBOARD_OLLAMA_MODEL="nombre-del-modelo-local"
   export OLLAMA_BASE_URL="http://127.0.0.1:11434"
   export DISBOARD_DATA_DIR="$HOME/.local/share/disboard"
   ```

   El backend de Disboard rechaza en modo privado direcciones Ollama que no sean `localhost`; no reenvíes el puerto de Ollama a la LAN.

4. Registra las personas autorizadas desde una terminal local. La llave se muestra una sola vez; entrégala por un canal privado:

   ```sh
   python disboard_users.py add Tet
   python disboard_users.py add colaborador
   python disboard_users.py list
   python disboard_users.py revoke colaborador
   ```

5. Para probar solo desde el laptop:

   ```sh
   python disboard_web.py
   ```

   Abre `http://127.0.0.1:8765`. Este modo loopback no es accesible desde otros dispositivos.

## Archivos locales y transferencia desde consola

La pestaña **Archivos** acepta archivos de hasta 50 MiB y los guarda en
`$DISBOARD_DATA_DIR/artifacts/<edge>/` (por defecto `.disboard-local/artifacts/`).
La lista muestra la ruta relativa y SHA-256; la descarga vuelve a verificar el hash.
Este almacén es privado y separado de `edge-*/`: subir no importa un PDF a la
bibliografía ni copia el archivo automáticamente a `docs/` o `data/`. La consola
puede ofrecer aportes textuales de este almacén al contexto, pero Tet debe
autorizarlo en cada ciclo y se comprueba el hash; no se adjuntan archivos binarios
a prompts.

Para mover un archivo entre Codespaces y el host personal sin publicar un puerto
en Internet, conecta ambos equipos a la misma VPN privada (por ejemplo, Tailscale
Personal, sujeto a los términos vigentes) y configura HTTPS válido en el host.
Con Tailscale Serve, sigue la guía oficial de Tailscale para exponer el servicio
local solo dentro del tailnet; no desactives la validación TLS ni abras el puerto
del servidor al router. La disponibilidad de una conexión directa depende de la
red; los relays de Tailscale pueden transportar tráfico cuando la conexión directa
no es posible. Codespaces requiere instalar/configurar el cliente Tailscale de
forma autorizada; el repositorio no lo une automáticamente al tailnet.

En el host personal, configura un token aleatorio de al menos 32 caracteres y
manténlo como secreto local; **no lo pongas en Git, argumentos visibles ni logs**:

```sh
python -c "import secrets; print(secrets.token_urlsafe(48))"
export DISBOARD_RELAY_TOKEN="valor-generado-en-canal-privado"
export DISBOARD_RELAY_URL="https://nombre-privado-del-host"
```

Configura el mismo `DISBOARD_RELAY_TOKEN` y la `DISBOARD_RELAY_URL` HTTPS como
secretos/variables del entorno remoto autorizado. Reinicia el backend local para
que habilite las rutas relay. Los comandos se ejecutan desde el entorno que tiene
el archivo fuente/destino; por ejemplo, en Codespaces:

```sh
python disboard_relay.py list edge-mi-proyecto
python disboard_relay.py upload edge-mi-proyecto results/informe.md ./informe.md
python disboard_relay.py download edge-mi-proyecto inputs/datos.csv ./datos.csv
```

`upload` copia el archivo hacia el almacén privado del host local; `download`
copia desde ese almacén al entorno que ejecuta el comando, verifica SHA-256 y no
sobrescribe un destino existente. Los IDs deben ser `edge-*` y las rutas son
relativas. Para instalar el cliente en un entorno sin dependencias, el proyecto
ya declara `requests` en `requirements.txt`.

Este relay es deliberadamente una **transferencia manual de artefactos**, no una
VPN incluida ni un ejecutor remoto: no inicia agentes, no crea paquetes de jobs,
no sincroniza resultados automáticamente con el repositorio `edge-*` y no elimina
copias del workspace remoto. Mientras trabajas en Codespaces, esos archivos
siguen estando también en una máquina cloud; decide qué puedes enviar y borra la
copia remota de acuerdo con la política aplicable. La VPN protege la ruta de red,
no cambia dónde corre el código ni quién puede acceder al host; el token bearer
permite acceso al almacén relay, por lo que debe protegerse y rotarse si se expone.

## Acceso desde la red local

No publiques el puerto en el router. Para acceso desde tablet/laptop, usa una VPN privada (por ejemplo, WireGuard o Tailscale) y TLS con un certificado válido para el nombre privado del anfitrión. También puedes usar TLS en una LAN confiable, instalar la autoridad certificadora local en cada dispositivo y limitar el puerto del firewall a esa subred. En todos los casos, protege la llave privada del certificado (`chmod 600`).

En laptop/desktop, se recomiendan Chrome o Edge estables y actualizados; Firefox actual es una alternativa prevista. En tabletas, usa Safari actualizado en iPadOS o Chrome actualizado en Android. Chrome para iPadOS utiliza WebKit, como los demás navegadores de esa plataforma. El workflow de CI está configurado para probar la interfaz en Chromium, Firefox y WebKit, incluida una vista estrecha de 390 px, con respuestas de API simuladas. Esto comprueba los motores web principales y el JavaScript de la interfaz, pero no certifica dispositivos reales, TLS/VPN, ni las diferencias de integración de Safari en iPadOS o Chrome en Android. No uses Internet Explorer ni navegadores sin soporte/actualizaciones.

Para ejecutar las pruebas opcionales de navegador localmente, instala el runner y sus tres motores; el backend se sustituye por respuestas simuladas:

```sh
python -m pip install -r requirements-browser.txt
python -m playwright install chromium firefox webkit
python tests/browser_smoke.py
```

La CI también renderiza los bloques Mermaid de `README.md` y `docs/architecture.md` usando Mermaid CLI y verifica que cada bloque produzca un SVG. Para repetir esa validación localmente, instala Node.js 20 o compatible y Mermaid CLI, y ejecuta:

```sh
npm install --global @mermaid-js/mermaid-cli@11.4.2
python tests/render_mermaid.py
```

```sh
python disboard_web.py --host 0.0.0.0 --port 8765 \
  --tls-certfile /ruta/privada/disboard.crt \
  --tls-keyfile /ruta/privada/disboard.key
```

Al conectarse, usa `https://` y el nombre/IP para el que se emitió el certificado. No aceptes avisos de certificado en dispositivos compartidos. Una VPN evita abrir el servicio a Internet público, pero el equipo anfitrión debe permanecer encendido.

## Grafo y privacidad

La secuencia web actual lee Elkia primero y luego el contrato del edge registrado; sigue con Sora (plan) → Jibril (síntesis opcional si el proyecto tiene notas locales) → Shiro (respuesta) → Kurami (crítica), con una corrección máxima de Shiro. LangGraph guarda checkpoints locales; la interfaz requiere aprobación humana y no modifica ni publica archivos.

El flujo web impone Ollama local y falla cerrado si no hay modelo configurado. Elkia, el contrato del proyecto y las notas `docs/bibliografia/*.md` seleccionadas se leen en el laptop y solo se envían al Ollama en `localhost`. No configures proveedores externos en esta interfaz con proyectos privados.

Las llaves se guardan como hashes scrypt; las sesiones usan tokens aleatorios revocables y cookies HttpOnly. Las bases privadas se guardan en `.disboard-local/` (o `DISBOARD_DATA_DIR`) con permisos restringidos. Conserva copias de seguridad cifradas y no subas esa carpeta al repositorio.

## Uso de tokens y cuotas

El panel Consumo suma tokens reportados por Ollama/SDK cuando están disponibles; de otro modo muestra una estimación aproximada por caracteres. Nunca guarda prompts. Los límites diarios son configurables en `exeed_config.json`; `null` significa que no se conoce el límite y no se muestra un porcentaje restante. El número no representa el saldo de la cuenta del proveedor.

## Almacenamiento híbrido y ubicaciones reales

La API de carga PDF especializada escribe la extracción y la copia del PDF bajo el proyecto `edge-*` del host que ejecuta el backend. La pestaña genérica Archivos usa el almacén privado, separado de ese flujo. Por ello:

- Con el backend ejecutándose en el laptop, una carga desde la tablet conectada llega al repositorio del laptop.
- Con el backend ejecutándose en Codespaces, la carga queda en el workspace remoto de Codespaces, no en el disco personal.
- La pestaña Archivos admite PDF, CSV, XLSX y otros tipos de archivo, pero no los interpreta por sí misma.
- Existe un relay de artefactos con TLS, token bearer, límite de tamaño, no-sobrescritura y verificación SHA-256. No realiza ejecución remota ni integra automáticamente los resultados dentro del edge.
- Para bibliografía, usa la ingestión PDF especializada, que preserva el original y extrae Markdown por página; la carga genérica no crea referencias ni dispara consultas DOI.
- Para mantener los agentes y datos sensibles en el equipo personal, ejecuta allí el backend/agentes y usa la tablet como cliente. El relay Codespaces→host personal es opcional y requiere que el operador configure VPN, TLS y secretos correctamente.

La sincronización por Git no debe usarse para datos privados, fuentes subidas ni dictámenes. GitHub es para código autorizado, no es el mecanismo de almacenamiento canónico de los documentos de investigación privados.

## Informes y bibliografía local

La interfaz web no es la única forma de operar Disboard. En Codespaces o desde una terminal con el repositorio y sus dependencias, ejecuta `python disboard_console.py` para iniciar el tablero de consola, elegir proyectos, ejecutar tareas y resolver el HITL. La consola usa las rutas de proveedores de `exeed_config.json`; a diferencia del tablero web, no fuerza Ollama local.

La extracción del texto de un PDF puede ejecutarse sin IA desde la consola:

```text
pdf edge-mi-proyecto "/ruta/al/articulo.pdf" 10.1234/doi-semilla
```

O directamente:

```sh
python disboard_pdf_to_markdown.py edge-mi-proyecto /ruta/al/articulo.pdf
```

Guarda una transcripción Markdown por página en `docs/bibliografia/` y copia el PDF original a `docs/bibliografia/fuentes/`. Esos archivos generados se excluyen de Git por defecto. No es una conversión visual sin pérdida: tablas, gráficos, formato, fórmulas y páginas escaneadas pueden no quedar representados por la extracción textual. El original se conserva; las páginas sin texto extraíble quedan marcadas para revisión/OCR.

Si se detecta un DOI semilla (o Tet lo proporciona explícitamente), la consola pregunta si puede enviar ese DOI a OpenAlex para localizar trabajos citantes. La búsqueda no transmite el PDF ni el contrato del edge. Cuando Ollama está configurado, Jibril evalúa localmente los metadatos y abstracts obtenidos frente al contrato; sin modelo, las propuestas quedan pendientes de evaluación. Se guardan en `docs/bibliografia/propuestas/` y no son visibles como bibliografía activa para los demás agentes hasta la aprobación explícita de Tet:

```text
aprobar-ref edge-mi-proyecto 10.xxxx/doi-propuesto
```

En la web, una ingesta PDF realiza la búsqueda pública solo si `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1`; su pestaña Bibliografía separa y permite aprobar propuestas. OpenAlex enumera los trabajos citantes; Crossref puede aportar metadatos y conteos agregados, no se usa aquí como lista de citantes. La web usa Ollama local.

En la consola, cada ciclo `continuar` pregunta antes de enviar contrato, peticiones u otros contextos a proveedores externos. La opción predeterminada es **Ollama local únicamente** y falla si no se configura `DISBOARD_OLLAMA_MODEL`; al autorizar proveedores externos, solo se incluye material adicional si también se autorizó incluirlo. `concluir` aplica el mismo consentimiento explícito para enviar el documento a un proveedor externo. Las observaciones de revisiones externas y el entregable se procesan solo con Ollama, y los paquetes de revisión quedan excluidos de Git por defecto.

Esta política reduce envíos a servicios externos, pero no convierte Codespaces en almacenamiento local al dispositivo: el workspace y Ollama corren dentro del entorno remoto de Codespaces. Para mantener los archivos en el disco físico del usuario, clona y ejecuta el repositorio en ese equipo, configura `DISBOARD_DATA_DIR` en una carpeta privada local y no subas datos, Markdown de PDFs ni dictámenes a Git. El contenido sí saldrá del equipo si Tet autoriza proveedores externos o búsquedas públicas por DOI; backups, sincronización de carpetas y telemetría del sistema anfitrión requieren controles propios.

El ensamblador de informes funciona sin IA y acepta un manifiesto JSON en el propio `edge`:

```sh
python disboard_reports.py edge-mi-proyecto --manifest docs/report-manifest.json --format tex --pdf
```

Duplica `docs/report-manifest.template.json` en ese proyecto y apunta a CSV, imágenes, metadatos y código exportado por Wolfram. Los informes incluyen hashes de los archivos fuente y limitan las tablas grandes.

Las notas bibliográficas pueden generarse con una referencia DOI o un PDF local:

```sh
python disboard_bibliography.py edge-mi-proyecto --doi 10.xxxx/xxxxx
python disboard_bibliography.py edge-mi-proyecto --pdf /ruta/local/articulo.pdf
```

Por privacidad, Crossref/OpenAlex no se consultan por defecto. Para permitir la consulta pública de metadatos de DOI, habilita explícitamente `DISBOARD_ALLOW_PUBLIC_DOI_LOOKUP=1`. El PDF se conserva bajo `docs/bibliografia/fuentes/` y se excluye de Git; solo se extrae y resume con el modelo local. PDFs escaneados requieren OCR local.

Los Markdown son portables y se pueden importar manualmente a NotebookLM junto con el PDF si Tet decide usar ese servicio. NotebookLM es externo y no debe recibir artículos o notas confidenciales sin autorización institucional.