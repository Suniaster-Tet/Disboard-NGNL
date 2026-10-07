const loginView = document.querySelector("#login-view");
const workspaceView = document.querySelector("#workspace-view");
const loginForm = document.querySelector("#login-form");
const loginMessage = document.querySelector("#login-message");
const runMessage = document.querySelector("#run-message");
const connectionState = document.querySelector("#connection-state");

async function request(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(path, {
    credentials: "same-origin",
    headers: isFormData ? options.headers : { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(payload.detail || "La solicitud no pudo completarse.");
  return payload;
}

function showMessage(element, text, isError = false) {
  element.textContent = text;
  element.classList.toggle("error", isError);
}

function showWorkspace(username) {
  loginView.hidden = true;
  workspaceView.hidden = false;
  document.querySelector("#user-label").textContent = username;
  loadProjects();
  loadUsage();
}

async function loadProjects() {
  try {
    const result = await request("/api/projects");
    const select = document.querySelector("#project-select");
    for (const project of result.projects) {
      const option = document.createElement("option");
      option.value = project.slug;
      option.textContent = project.name;
      select.append(option);
    }
  } catch (error) {
    showMessage(runMessage, error.message, true);
  }
}

async function initialize() {
  try {
    const status = await request("/api/status");
    connectionState.textContent = status.inference_mode === "local-only" ? "Solo red local" : "Revisar privacidad";
    document.querySelector("#model-state").textContent = status.local_model_configured
      ? "Ollama configurado · solo local"
      : "Falta configurar Ollama";
    const doiNotice = document.querySelector("#bibliography-message");
    if (!status.public_doi_lookup_enabled) {
      doiNotice.textContent = "Modo privado: DOI y PDF no generan consultas externas. Activa la búsqueda pública solo cuando la autorices.";
    }
    if (status.registered_users === 0) {
      showMessage(loginMessage, "No hay usuarios registrados. Añádelos desde el laptop anfitrión.", true);
      return;
    }
    try {
      const session = await request("/api/session");
      showWorkspace(session.username);
    } catch {
      loginView.hidden = false;
    }
  } catch {
    connectionState.textContent = "Servidor no disponible";
    showMessage(loginMessage, "No se pudo conectar con el servidor local.", true);
  }
}

function selectTab(name) {
  for (const button of document.querySelectorAll(".console-tab")) {
    const selected = button.dataset.tab === name;
    button.classList.toggle("active", selected);
    button.setAttribute("aria-selected", String(selected));
    document.querySelector(`#panel-${button.dataset.tab}`).hidden = !selected;
  }
  if (name === "usage") loadUsage();
  if (name === "bibliography") loadBibliography();
  if (name === "artifacts") loadArtifacts();
}

async function loadArtifacts() {
  const project = document.querySelector("#project-select").value;
  const target = document.querySelector("#artifact-list");
  if (!project) {
    target.textContent = "Selecciona un proyecto para consultar sus archivos.";
    return;
  }
  try {
    const result = await request(`/api/artifacts?project=${encodeURIComponent(project)}`);
    target.replaceChildren();
    if (!result.artifacts.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Este proyecto aún no tiene archivos en el almacén local.";
      target.append(empty);
      return;
    }
    for (const artifact of result.artifacts) {
      const item = document.createElement("article");
      item.className = "bibliography-note";
      const heading = document.createElement("h2");
      heading.textContent = artifact.path;
      const details = document.createElement("p");
      details.className = "panel-caption";
      details.textContent = `${artifact.size.toLocaleString()} bytes · SHA-256 ${artifact.sha256}`;
      const download = document.createElement("a");
      download.className = "primary";
      download.href = `/api/artifacts/download?project=${encodeURIComponent(project)}&path=${encodeURIComponent(artifact.path)}`;
      download.textContent = "Descargar archivo";
      item.append(heading, details, download);
      target.append(item);
    }
  } catch (error) {
    target.textContent = error.message;
  }
}

async function loadBibliography() {
  const project = document.querySelector("#project-select").value;
  const target = document.querySelector("#bibliography-list");
  if (!project) {
    target.textContent = "Selecciona un proyecto para consultar sus notas.";
    return;
  }
  try {
    const result = await request(`/api/bibliography?project=${encodeURIComponent(project)}`);
    target.replaceChildren();
    if (!result.notes.length && !result.proposals.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Este proyecto aún no tiene notas bibliográficas.";
      target.append(empty);
      return;
    }
    for (const note of [
      ...result.notes.map((item) => ({ ...item, proposal: false })),
      ...result.proposals.map((item) => ({ ...item, proposal: true })),
    ]) {
      const article = document.createElement("article");
      article.className = "bibliography-note";
      const heading = document.createElement("h2");
      heading.textContent = `${note.proposal ? "Propuesta · " : ""}${note.path}`;
      const content = document.createElement("pre");
      content.textContent = note.markdown;
      article.append(heading, content);
      if (note.proposal) {
        for (const doi of note.pending_dois) {
          const approve = document.createElement("button");
          approve.className = "secondary";
          approve.type = "button";
          approve.textContent = `Aprobar referencia ${doi}`;
          approve.addEventListener("click", async () => {
            try {
              await request("/api/bibliography/approve", {
                method: "POST",
                body: JSON.stringify({
                  project,
                  doi,
                }),
              });
              showMessage(document.querySelector("#bibliography-message"), `Referencia aprobada: ${doi}`);
              loadBibliography();
            } catch (error) {
              showMessage(document.querySelector("#bibliography-message"), error.message, true);
            }
          });
          article.append(approve);
        }
      }
      target.append(article);
    }
  } catch (error) {
    target.textContent = error.message;
  }
}

async function loadUsage() {
  const agent = document.querySelector("#agent-filter").value;
  const target = document.querySelector("#usage-cards");
  try {
    const result = await request(`/api/usage${agent ? `?agent=${encodeURIComponent(agent)}` : ""}`);
    const filter = document.querySelector("#agent-filter");
    if (filter.options.length === 1) {
      for (const name of result.agents) {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name.replace(/\b\w/g, (letter) => letter.toUpperCase());
        filter.append(option);
      }
    }
    target.replaceChildren();
    if (!result.usage.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Sin llamadas registradas en las últimas 24 horas.";
      target.append(empty);
      return;
    }
    for (const row of result.usage) {
      const card = document.createElement("article");
      card.className = "usage-card";
      const title = document.createElement("div");
      title.className = "usage-card-title";
      const name = document.createElement("strong");
      name.textContent = row.agent;
      const model = document.createElement("span");
      model.textContent = `${row.provider} · ${row.model}`;
      title.append(name, model);
      const total = row.input_tokens + row.output_tokens;
      const count = document.createElement("p");
      count.className = "usage-total";
      count.textContent = `${total.toLocaleString()} tokens · ${row.requests} solicitudes`;
      const limit = result.limits[row.provider]?.daily_tokens;
      if (Number.isFinite(limit) && limit > 0) {
        const percent = Math.min(100, total / limit * 100);
        const meter = document.createElement("progress");
        meter.max = 100;
        meter.value = percent;
        meter.setAttribute("aria-label", `${percent.toFixed(1)} por ciento del límite configurado`);
        const remaining = document.createElement("span");
        remaining.className = "usage-remaining";
        remaining.textContent = `${percent.toFixed(1)}% usado · ${Math.max(0, limit - total).toLocaleString()} restantes según límite configurado`;
        card.append(title, count, meter, remaining);
      } else {
        const limitNote = document.createElement("span");
        limitNote.className = "usage-remaining";
        limitNote.textContent = "Límite no configurado · restante no disponible";
        card.append(title, count, limitNote);
      }
      const quality = document.createElement("span");
      quality.className = "usage-source";
      quality.textContent = `${row.reported_requests} reportadas · ${row.estimated_requests} estimadas`;
      card.append(quality);
      target.append(card);
    }
  } catch (error) {
    target.textContent = error.message;
  }
}

for (const button of document.querySelectorAll(".console-tab")) {
  button.addEventListener("click", () => selectTab(button.dataset.tab));
}
document.querySelector("#agent-filter").addEventListener("change", loadUsage);
document.querySelector("#project-select").addEventListener("change", () => {
  const activeTab = document.querySelector(".console-tab.active")?.dataset.tab;
  if (activeTab === "artifacts") loadArtifacts();
  if (activeTab === "bibliography") loadBibliography();
});

document.querySelector("#artifact-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.currentTarget;
  const file = document.querySelector("#artifact-input").files[0];
  const project = document.querySelector("#project-select").value;
  const message = document.querySelector("#artifact-message");
  if (!project || !file) {
    showMessage(message, "Selecciona un proyecto y un archivo.", true);
    return;
  }
  if (file.size > 50 * 1024 * 1024) {
    showMessage(message, "El archivo supera el límite de 50 MB.", true);
    return;
  }
  const body = new FormData();
  body.append("project", project);
  body.append("file", file);
  try {
    const result = await request("/api/artifacts", { method: "POST", body });
    showMessage(message, `Guardado en el host como ${result.path} · SHA-256 ${result.sha256}`);
    form.reset();
    loadArtifacts();
  } catch (error) {
    showMessage(message, error.message, true);
  }
});

document.querySelector("#doi-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.querySelector("#bibliography-message");
  try {
    const result = await request("/api/bibliography/doi", {
      method: "POST",
      body: JSON.stringify({
        project: document.querySelector("#project-select").value,
        doi: document.querySelector("#doi-input").value.trim(),
      }),
    });
    showMessage(message, `Ficha creada en ${result.source}`);
    document.querySelector("#doi-input").value = "";
    loadBibliography();
  } catch (error) {
    showMessage(message, error.message, true);
  }
});

document.querySelector("#pdf-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = document.querySelector("#bibliography-message");
  const file = document.querySelector("#pdf-input").files[0];
  if (!document.querySelector("#project-select").value) {
    showMessage(message, "Selecciona un proyecto edge antes de ingresar la fuente.", true);
    return;
  }
  if (!file) return;
  const form = new FormData();
  form.set("project", document.querySelector("#project-select").value);
  form.set("file", file);
  showMessage(message, "Leyendo PDF de forma local…");
  try {
    const result = await request("/api/bibliography/pdf", { method: "POST", body: form });
    showMessage(message, `Notas creadas en ${result.source}`);
    document.querySelector("#pdf-input").value = "";
    loadBibliography();
  } catch (error) {
    showMessage(message, error.message, true);
  }
});

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  showMessage(loginMessage, "Verificando acceso…");
  const username = document.querySelector("#username").value.trim();
  const keyInput = document.querySelector("#access-key");
  const accessKey = keyInput.value;
  try {
    const session = await request("/api/login", {
      method: "POST",
      body: JSON.stringify({ username, access_key: accessKey }),
    });
    keyInput.value = "";
    showWorkspace(session.username);
  } catch (error) {
    keyInput.value = "";
    showMessage(loginMessage, error.message, true);
  }
});

document.querySelector("#logout-button").addEventListener("click", async () => {
  try { await request("/api/logout", { method: "POST", body: "{}" }); } catch { /* End local view regardless. */ }
  workspaceView.hidden = true;
  loginView.hidden = false;
});

document.querySelector("#run-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = document.querySelector("#run-button");
  button.disabled = true;
  showMessage(runMessage, "Los agentes están trabajando en el laptop anfitrión…");
  document.querySelector("#result").hidden = true;
  document.querySelector("#outputs-empty").hidden = false;
  const chatHistory = document.querySelector("#chat-history");
  if (chatHistory.querySelector(".empty-state")) chatHistory.replaceChildren();
  const question = document.createElement("p");
  question.className = "chat-message user-message";
  question.textContent = document.querySelector("#task-input").value;
  chatHistory.append(question);
  try {
    const result = await request("/api/runs", {
      method: "POST",
      body: JSON.stringify({
        task: document.querySelector("#task-input").value,
        project: document.querySelector("#project-select").value,
      }),
    });
    document.querySelector("#plan-output").textContent = result.plan;
    document.querySelector("#draft-output").textContent = result.draft;
    document.querySelector("#review-output").textContent = result.review || "Sin observaciones registradas.";
    document.querySelector("#run-status").textContent = result.approved_by_agent ? "REVISIÓN DE AGENTES: APROBADA" : "REVISIÓN HUMANA PENDIENTE";
    document.querySelector("#revision-count").textContent = `${result.revisions} correcciones`;
    document.querySelector("#result").hidden = false;
    document.querySelector("#outputs-empty").hidden = true;
    const reply = document.createElement("p");
    reply.className = "chat-message agent-message";
    reply.textContent = "Ejecución terminada. El equipo dejó una propuesta en Salidas.";
    chatHistory.append(reply);
    const activity = document.querySelector("#activity-log");
    activity.replaceChildren();
    for (const event of result.trace) {
      const item = document.createElement("li");
      const agent = document.createElement("strong");
      agent.textContent = event.agent;
      const stage = document.createElement("span");
      stage.textContent = event.stage;
      const state = document.createElement("em");
      state.textContent = event.status;
      item.append(agent, stage, state);
      activity.append(item);
    }
    showMessage(runMessage, "Flujo terminado. La aprobación final sigue siendo tuya.");
    selectTab("outputs");
    loadUsage();
  } catch (error) {
    showMessage(runMessage, error.message, true);
  } finally {
    button.disabled = false;
  }
});

initialize();