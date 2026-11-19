"use strict";

const $ = (id) => document.getElementById(id);
const labels = { draft: "Sin preparar", active: "En curso", paused: "Pausado", review: "En revisión", completed: "Terminado" };
const kindLabels = { document: "DOCUMENTACIÓN", review: "REVISIÓN TÉCNICA", research: "INVESTIGACIÓN" };
const examples = {
  document: ["Documentar la instalación", "Preparar una guía de instalación de BABYLON-60 con los pasos de inicio, las fuentes de consulta y los límites de la distribución actual."],
  review: ["Revisar la arquitectura", "Preparar una revisión de la arquitectura de BABYLON-60. Separar el diseño propuesto, lo observado en las fuentes y las comprobaciones que siguen pendientes."],
  research: ["Preparar una investigación", "Organizar las fuentes y las preguntas pendientes para investigar cómo conectar Babylon Work con el motor de BABYLON-60."],
};
let token = sessionStorage.getItem("babylon-work-access") || "";
const access = new URLSearchParams(location.hash.slice(1)).get("access");
if (access) {
  token = access;
  sessionStorage.setItem("babylon-work-access", token);
  history.replaceState(null, "", location.pathname);
}
let tasks = [], sources = [], current = null, dirty = false, busy = false, editing = false, toastTimer;

function node(tag, value, className) {
  const element = document.createElement(tag);
  if (value !== undefined) element.textContent = value;
  if (className) element.className = className;
  return element;
}

function message(value) {
  $("toast").textContent = value;
  $("toast").hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => { $("toast").hidden = true; }, 3500);
}

function error(value) {
  $("notice").textContent = value;
  $("notice").hidden = false;
}

async function api(path, body) {
  const response = await fetch(path, {
    method: body ? "POST" : "GET",
    headers: { Authorization: `Bearer ${token}`, ...(body ? { "Content-Type": "application/json" } : {}) },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });
  const data = await response.json();
  if (!response.ok) {
    if (response.status === 401 && !$("access-dialog").open) $("access-dialog").showModal();
    throw new Error(data.error || "No se ha podido completar la operación.");
  }
  return data;
}

async function run(operation) {
  if (busy) return;
  busy = true;
  document.body.setAttribute("aria-busy", "true");
  $("document-editor").readOnly = true;
  $("notice").hidden = true;
  try { await operation(); }
  catch (failure) { error(failure.message || "No se ha podido conectar con el servidor local."); }
  finally {
    busy = false;
    $("document-editor").readOnly = current?.status === "completed";
    document.body.removeAttribute("aria-busy");
  }
}

function date(value) {
  return new Intl.DateTimeFormat("es-ES", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit" }).format(new Date(value));
}

function canLeave() {
  return !dirty || window.confirm("Hay cambios sin guardar. ¿Quieres descartarlos para cambiar de vista?");
}

function showView(name) {
  for (const view of ["tasks", "task", "sources", "about"]) $(view + "-view").hidden = view !== name;
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("selected", button.dataset.view === (name === "task" ? "tasks" : name));
  });
  $("breadcrumb").textContent = `Mi espacio / ${ { tasks: "Encargos", task: "Mesa de trabajo", sources: "Fuentes", about: "Conexiones" }[name] }`;
}

function statusBadge(task) {
  const badge = node("span", labels[task.status], "status");
  badge.dataset.status = task.status;
  return badge;
}

function renderTasks() {
  $("task-count").textContent = tasks.length;
  $("empty-state").hidden = tasks.length > 0;
  $("saved-count").textContent = `${tasks.length} ${tasks.length === 1 ? "encargo guardado" : "encargos guardados"} en este equipo`;
  $("task-list").replaceChildren();
  $("recent-tasks").replaceChildren();
  for (const task of tasks) {
    const button = node("button", undefined, "task-row");
    const info = node("span");
    info.append(node("strong", task.title), node("small", `${kindLabels[task.kind]} · ${date(task.updated_at)}`));
    button.append(node("span", "▤", "task-icon"), info, statusBadge(task));
    button.addEventListener("click", () => { if (canLeave()) run(() => openTask(task.id)); });
    $("task-list").append(button);
  }
  for (const task of tasks.slice(0, 7)) {
    const button = node("button", task.title, "recent-button");
    button.classList.toggle("active", current?.id === task.id);
    button.addEventListener("click", () => { if (canLeave()) run(() => openTask(task.id)); });
    $("recent-tasks").append(button);
  }
}

function renderMarkdown(value) {
  const article = $("document-preview");
  article.replaceChildren();
  let paragraph = [], code = null, list = null;
  function inline(tag, value) {
    const element = node(tag);
    const tokens = /(\*\*[^*]+\*\*|`[^`]+`)/g;
    let end = 0;
    for (const match of value.matchAll(tokens)) {
      element.append(document.createTextNode(value.slice(end, match.index)));
      const bold = match[0].startsWith("**");
      element.append(node(bold ? "strong" : "code", match[0].slice(bold ? 2 : 1, bold ? -2 : -1)));
      end = match.index + match[0].length;
    }
    element.append(document.createTextNode(value.slice(end)));
    return element;
  }
  function flush() {
    if (paragraph.length) { article.append(inline("p", paragraph.join("\n"))); paragraph = []; }
    list = null;
  }
  for (const line of value.split("\n")) {
    if (line.startsWith("```")) {
      flush();
      if (code) code = null;
      else { code = node("pre", ""); article.append(code); }
    } else if (code) code.textContent += line + "\n";
    else if (/^#{1,3} /.test(line)) {
      flush();
      const depth = line.indexOf(" ");
      article.append(inline(`h${depth}`, line.slice(depth + 1)));
    } else if (line.startsWith("- ")) {
      if (paragraph.length) flush();
      if (!list) { list = node("ul"); article.append(list); }
      list.append(inline("li", line.slice(2)));
    } else if (line.startsWith("> ")) {
      flush(); article.append(inline("blockquote", line.slice(2)));
    } else if (line.trim() === "") flush();
    else paragraph.push(line);
  }
  flush();
}

function setMode(edit) {
  editing = edit;
  $("document-editor").hidden = !edit;
  $("document-preview").hidden = edit;
  $("edit-mode").setAttribute("aria-pressed", String(edit));
  $("preview-mode").setAttribute("aria-pressed", String(!edit));
  if (!edit) renderMarkdown($("document-editor").value);
}

function setTab(name) {
  for (const tab of ["document", "context", "activity", "runs"]) {
    $("panel-" + tab).hidden = tab !== name;
    $("tab-" + tab).setAttribute("aria-selected", String(tab === name));
  }
}

function renderTask() {
  dirty = false;
  $("task-title").textContent = current.title;
  $("task-kind").textContent = kindLabels[current.kind];
  $("task-goal").textContent = current.prompt;
  $("task-status").textContent = labels[current.status];
  $("task-status").dataset.status = current.status;
  const hasDocument = Boolean(current.document.trim());
  $("prepare-state").hidden = hasDocument;
  $("document-state").hidden = !hasDocument;
  $("document-editor").value = current.document;
  $("document-editor").readOnly = current.status === "completed";
  $("document-name").textContent = filename();
  $("save-state").textContent = `Guardado · revisión ${current.revision}`;
  $("save-document").disabled = true;
  $("export-task").disabled = !hasDocument;
  $("pause-task").textContent = current.status === "paused" || current.status === "draft" ? "Retomar" : "Pausar";
  $("pause-task").hidden = current.status === "completed";
  $("complete-task").textContent = current.status === "completed" ? "Reabrir encargo ↗" : "Terminar revisión ✓";
  $("complete-task").disabled = !hasDocument;
  $("decision-form").hidden = current.status === "completed";
  $("next-step").textContent = { draft: "Prepara el primer borrador con las fuentes del proyecto.", active: "El contexto está recuperado. Continúa preparando o revisando el documento.", review: "Revisa el borrador, completa lo que falta y confirma el resultado.", paused: "Retoma el encargo con el documento y sus decisiones conservados.", completed: "El documento tiene tu revisión. Puedes exportarlo o reabrirlo." }[current.status];
  $("decision-list").replaceChildren();
  if (!current.decisions.length) $("decision-list").append(node("p", "Todavía no hay decisiones guardadas.", "quiet"));
  current.decisions.forEach((decision) => $("decision-list").append(node("div", decision, "decision-item")));
  $("activity-list").replaceChildren();
  for (const event of current.events) {
    const item = node("li", event.detail);
    const time = node("time", date(event.created_at));
    time.dateTime = event.created_at;
    item.append(time);
    $("activity-list").append(item);
  }
  $("task-sources").replaceChildren();
  if (!current.sources.length) $("task-sources").append(node("p", "Se registrarán al preparar el documento.", "quiet"));
  for (const source of current.sources) {
    const button = node("button", source.label, "rail-source");
    button.append(node("span", `BLAKE3 ${source.digest.slice(0, 12)}…`));
    button.addEventListener("click", () => run(() => openSource(source.id, source.digest)));
    $("task-sources").append(button);
  }
  setMode(editing && current.status !== "completed");
  renderTasks();
  if (typeof loadRuns === "function") loadRuns().catch((failure) => error(failure.message));
}

async function openTask(id) {
  current = await api("/api/tasks/" + id);
  localStorage.setItem("babylon-work-last-task", id);
  renderTask();
  setTab("document");
  showView("task");
}

async function refresh() {
  const data = await api("/api/workspace");
  tasks = data.tasks;
  sources = data.sources;
  renderTasks();
  $("connection-label").textContent = "Espacio local conectado";
  $("connection-dot").classList.remove("offline");
  $("source-list").replaceChildren();
  for (const source of sources) {
    const button = node("button", undefined, "source-row");
    const info = node("span");
    info.append(node("strong", source.label), node("small", source.path));
    button.append(info, node("span", "↗"));
    button.addEventListener("click", () => run(() => openSource(source.id)));
    $("source-list").append(button);
  }
}

async function openSource(id, expectedDigest) {
  const source = await api("/api/sources/" + id);
  $("source-title").textContent = source.label;
  $("source-path").textContent = source.path;
  $("source-digest").textContent = `BLAKE3 ${source.digest}${expectedDigest && source.digest !== expectedDigest ? " · ATENCIÓN: la fuente ha cambiado desde el borrador." : ""}`;
  $("source-content").textContent = source.content;
  $("source-dialog").showModal();
}

async function change(action, fields = {}) {
  current = await api("/api/tasks/" + current.id, { action, revision: current.revision, ...fields });
  await refresh();
  renderTask();
}

async function createTask(title, prompt, kind) {
  const task = await api("/api/tasks", { title, prompt, kind });
  await refresh();
  await openTask(task.id);
  message("Encargo creado. Su contexto se guardará aquí.");
}

function filename() {
  return (current.title.normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "").slice(0, 70) || "documento") + ".md";
}

function newDialog(kind = "document", preset) {
  $("new-form").reset();
  $("new-kind").value = kind;
  if (preset) { $("new-title").value = preset[0]; $("new-prompt").value = preset[1]; }
  $("new-dialog").showModal();
}

$("new-task").addEventListener("click", () => newDialog());
$("new-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (!canLeave()) return;
  run(async () => {
    await createTask($("new-title").value, $("new-prompt").value, $("new-kind").value);
    $("new-dialog").close();
  });
});
$("quick-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const prompt = $("quick-prompt").value.trim();
  if (!prompt) return;
  run(() => createTask(prompt.slice(0, 100), prompt, "document"));
});
document.querySelectorAll("[data-example]").forEach((button) => {
  button.addEventListener("click", () => newDialog(button.dataset.example, examples[button.dataset.example]));
});
document.querySelectorAll("[data-close]").forEach((button) => {
  button.addEventListener("click", () => $(button.dataset.close).close());
});
document.querySelectorAll("[data-view]").forEach((button) => {
  button.addEventListener("click", () => { if (canLeave()) { dirty = false; showView(button.dataset.view); } });
});
$("home").addEventListener("click", (event) => {
  event.preventDefault();
  if (canLeave()) { dirty = false; showView("tasks"); }
});
$("back-tasks").addEventListener("click", () => { if (canLeave()) { dirty = false; showView("tasks"); } });
document.querySelectorAll("[data-tab]").forEach((button) => button.addEventListener("click", () => setTab(button.dataset.tab)));
$("prepare-task").addEventListener("click", () => run(async () => { await change("prepare"); message("Borrador preparado con fuentes locales. Revisa su contenido."); }));
$("edit-mode").addEventListener("click", () => setMode(true));
$("preview-mode").addEventListener("click", () => setMode(false));
$("document-editor").addEventListener("input", () => {
  dirty = $("document-editor").value !== current.document;
  $("save-document").disabled = !dirty;
  $("save-state").textContent = dirty ? "Cambios sin guardar" : "Guardado localmente";
});
$("save-document").addEventListener("click", () => run(async () => {
  await change("save", { document: $("document-editor").value });
  message("Documento guardado.");
}));
$("pause-task").addEventListener("click", () => {
  if (dirty) { error("Guarda los cambios antes de pausar o retomar el encargo."); return; }
  run(async () => { await change(["draft", "paused"].includes(current.status) ? "resume" : "pause"); message(labels[current.status]); });
});
$("complete-task").addEventListener("click", () => {
  if (dirty) { error("Guarda el documento antes de terminar la revisión."); return; }
  if (current.status === "completed") run(() => change("reopen"));
  else { $("complete-form").reset(); $("complete-dialog").showModal(); }
});
$("complete-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(async () => { await change("complete", { reviewed: $("reviewed").checked }); $("complete-dialog").close(); message("Encargo terminado con tu revisión."); });
});
$("decision-form").addEventListener("submit", (event) => {
  event.preventDefault();
  if (dirty) { error("Guarda el documento antes de añadir una decisión."); return; }
  run(async () => { await change("decision", { decision: $("decision-input").value }); $("decision-form").reset(); message("Decisión guardada en el contexto."); });
});
$("export-task").addEventListener("click", () => {
  if (dirty) { error("Guarda los cambios antes de exportar."); return; }
  const url = URL.createObjectURL(new Blob([current.document], { type: "text/markdown;charset=utf-8" }));
  const link = node("a");
  link.href = url; link.download = filename(); link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
  message("Documento preparado para descargar.");
});
$("access-form").addEventListener("submit", (event) => {
  event.preventDefault();
  token = $("access-key").value.trim();
  run(async () => { await refresh(); sessionStorage.setItem("babylon-work-access", token); $("access-dialog").close(); $("access-key").value = ""; });
});
window.addEventListener("beforeunload", (event) => { if (dirty) { event.preventDefault(); event.returnValue = ""; } });
document.addEventListener("keydown", (event) => {
  if ((event.metaKey || event.ctrlKey) && event.key === "s" && current) {
    event.preventDefault();
    if (dirty) $("save-document").click();
  }
  if (event.key.toLowerCase() === "n" && !event.metaKey && !event.ctrlKey && !event.altKey &&
      !["INPUT", "TEXTAREA", "SELECT"].includes(document.activeElement.tagName) && !document.querySelector("dialog[open]")) newDialog();
});

run(async () => {
  try {
    await refresh();
    const last = localStorage.getItem("babylon-work-last-task");
    if (last && tasks.some((task) => task.id === last)) await openTask(last);
  } catch (failure) {
    $("connection-label").textContent = "Sin conexión";
    $("connection-dot").classList.add("offline");
    throw failure;
  }
});
