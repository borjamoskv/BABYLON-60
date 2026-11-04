"use strict";

let runtimeInfo = null, runsTimer, runtimeTimer;
const trackedRuns = new Set();
const runLabels = { queued: "En cola", running: "En curso", awaiting_approval: "Firma pendiente", authorizing: "Autorizando",
  succeeded: "Terminado", failed: "Fallido", denied: "Denegado", unknown: "Resultado no confirmado",
  interrupted: "Interrumpido", conflict: "Resultado conservado", incomplete: "Resultado parcial", needs_review: "Revisión necesaria" };

async function loadRuntime() {
  runtimeInfo = await api("/api/runtime");
  const providers = runtimeInfo.providers;
  const ready = providers.filter((provider) => provider.status === "ready");
  $("model-summary").textContent = !runtimeInfo.ready ? "Detectando conexiones de IA…" :
    ready.length ? `${ready.reduce((sum, item) => sum + item.models.length, 0)} modelos disponibles` : "Sin modelos disponibles";
  $("run-ai").disabled = $("prepare-ai").disabled = !ready.length;
  $("ai-provider").replaceChildren();
  for (const provider of ready) {
    const option = node("option", provider.label); option.value = provider.id;
    $("ai-provider").append(option);
  }
  const previousProvider = localStorage.getItem("babylon-work-provider");
  if (ready.some((provider) => provider.id === previousProvider)) $("ai-provider").value = previousProvider;
  updateModels();
  $("check-command").replaceChildren();
  for (const command of runtimeInfo.effects.commands) {
    const option = node("option", command.label); option.value = command.id;
    $("check-command").append(option);
  }
  $("prepare-checks").disabled = !runtimeInfo.effects.native_available || !runtimeInfo.effects.commands.length;
  $("checks-help").textContent = runtimeInfo.effects.native_available ?
    runtimeInfo.effects.signing_key_configured ? "Se mostrará la solicitud exacta antes de pedir la firma biométrica." :
      "Puedes preparar la solicitud. Para ejecutarla falta la clave pública de confianza del operador." : runtimeInfo.effects.detail;
  $("runtime-connections").replaceChildren();
  const connections = [...providers.map((provider) => ({ label: provider.label, detail: provider.detail,
    good: provider.status === "ready", status: { ready: "Disponible", unauthorized: "Credencial rechazada",
      unconfigured: "Sin configurar", unavailable: "No disponible", no_models: "Sin modelos" }[provider.status] })),
    { label: "Broker nativo de BABYLON-60", detail: runtimeInfo.effects.detail,
      good: runtimeInfo.effects.native_available, status: runtimeInfo.effects.native_available ? "Conectado" : "No disponible" }];
  for (const connection of connections) {
    const row = node("div", undefined, "capability"), description = node("div");
    description.append(node("h2", connection.label), node("p", connection.detail));
    row.append(description, node("span", connection.status, "status" + (connection.good ? "" : " pending")));
    $("runtime-connections").append(row);
  }
  $("signing-setup").textContent = runtimeInfo.effects.signing_key_configured ?
    "Hay una clave pública P-256 provisionada. Cada operación solicitará una firma nueva para su solicitud exacta." :
    "Falta la clave pública P-256 de confianza. La ejecución protegida se rechaza antes de intentar la biometría.";
  $("signing-status").textContent = runtimeInfo.effects.signing_key_configured ? "Provisionada" : "Pendiente";
  if (!runtimeInfo.ready) runtimeTimer = setTimeout(() => loadRuntime().catch((failure) => error(failure.message)), 1000);
}

function updateModels() {
  const provider = runtimeInfo?.providers.find((item) => item.id === $("ai-provider").value);
  $("ai-model").replaceChildren();
  for (const name of provider?.models || []) {
    const option = node("option", name); option.value = name; $("ai-model").append(option);
  }
  const previous = localStorage.getItem("babylon-work-model");
  if (provider?.models.includes(previous)) $("ai-model").value = previous;
  $("ai-location").textContent = provider?.detail || "No hay una conexión disponible.";
}

function openAIJob() {
  if (!current || current.status === "completed") { error("Abre un encargo en curso antes de trabajar con IA."); return; }
  if (dirty) { error("Guarda el documento antes de iniciar un trabajo con IA."); return; }
  $("ai-instruction").value = "";
  $("ai-dialog").showModal();
}

async function loadRuns() {
  clearTimeout(runsTimer);
  if (!current) return;
  const taskId = current.id;
  const jobs = await api(`/api/tasks/${taskId}/runs`);
  if (current?.id !== taskId) return;
  const hasActive = jobs.some((job) => ["queued", "running", "authorizing"].includes(job.state));
  $("pause-task").disabled = hasActive;
  $("run-ai").disabled = $("prepare-ai").disabled = hasActive || current.status === "completed" ||
    !runtimeInfo?.providers.some((provider) => provider.status === "ready");
  $("runs-list").replaceChildren();
  if (!jobs.length) $("runs-list").append(node("p", "Los trabajos de IA y las solicitudes de ejecución aparecerán aquí.", "quiet"));
  let reload = false;
  for (const job of jobs) {
    const active = ["queued", "running", "authorizing"].includes(job.state);
    if (active) trackedRuns.add(job.id);
    else if (trackedRuns.delete(job.id)) {
      message(job.detail || runLabels[job.state]);
      if (job.kind === "generation" && job.state === "succeeded") reload = true;
    }
    const row = node("section", undefined, "run-card");
    const heading = node("div", undefined, "run-heading");
    heading.append(node("strong", job.kind === "generation" ? `IA · ${job.model}` : "Comprobación protegida"),
      node("span", runLabels[job.state], "status" + (["succeeded"].includes(job.state) ? "" : " pending")));
    row.append(heading, node("p", job.detail || "Esperando al servidor local.", "quiet"));
    if (job.command) row.append(node("pre", job.command.join(" "), "run-command"));
    if (job.approval_task) {
      const details = node("details");
      details.append(node("summary", "Ver solicitud exacta"), node("pre", JSON.stringify(job.approval_task, null, 2)));
      row.append(details);
    }
    if (job.state === "awaiting_approval") {
      const authorize = node("button", "Solicitar firma y ejecutar", "primary");
      authorize.disabled = !runtimeInfo?.effects.signing_key_configured;
      authorize.addEventListener("click", () => run(async () => {
        if (dirty) throw new Error("Guarda el documento antes de solicitar la firma.");
        await api(`/api/runs/${job.id}/authorize`, {});
        trackedRuns.add(job.id);
        await loadRuns();
      }));
      row.append(authorize);
      if (!runtimeInfo?.effects.signing_key_configured) row.append(node("p", "Falta provisionar la clave del operador. Consulta Conexiones y alcance.", "quiet"));
    }
    if (job.result.output) row.append(node("pre", job.result.output, "run-output"));
    for (const warning of job.result.warnings || []) row.append(node("p", warning, "quiet"));
    if (["conflict", "incomplete", "needs_review"].includes(job.state) && job.result.document) {
      const open = node("button", "Ver el documento conservado", "secondary");
      open.addEventListener("click", () => { $("run-result").value = job.result.document; $("run-result-dialog").showModal(); });
      row.append(open);
    }
    if (job.result.usage) {
      const usage = job.result.usage;
      const counts = [usage.input_tokens, usage.output_tokens];
      if (counts.every((value) => Number.isInteger(value))) row.append(node("p", `Uso informado: ${counts[0]} tokens de entrada · ${counts[1]} de salida.`, "quiet"));
    }
    $("runs-list").append(row);
  }
  if (jobs.some((job) => ["queued", "running", "authorizing"].includes(job.state))) {
    runsTimer = setTimeout(() => loadRuns().catch((failure) => error(failure.message)), 1000);
  }
  if (reload) {
    if (dirty) { error("La IA ha guardado un resultado. Conserva tus cambios sin guardar antes de recargar el encargo."); return; }
    const updated = await api(`/api/tasks/${taskId}`);
    if (current?.id !== taskId || dirty) return;
    current = updated;
    await refresh();
    if (current?.id !== taskId || dirty) return;
    renderTask();
    setTab("document");
  }
}

$("run-ai").addEventListener("click", openAIJob);
$("prepare-ai").addEventListener("click", openAIJob);
$("ai-provider").addEventListener("change", updateModels);
$("ai-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(async () => {
    const provider = $("ai-provider").value, model = $("ai-model").value;
    const job = await api(`/api/tasks/${current.id}/runs`, { kind: "generation", revision: current.revision,
      provider, model, instruction: $("ai-instruction").value });
    localStorage.setItem("babylon-work-provider", provider);
    localStorage.setItem("babylon-work-model", model);
    trackedRuns.add(job.id);
    $("ai-dialog").close();
    setTab("runs");
    await loadRuns();
  });
});
$("checks-form").addEventListener("submit", (event) => {
  event.preventDefault();
  run(async () => {
    if (!current || dirty) throw new Error("Guarda el documento antes de preparar la comprobación.");
    const job = await api(`/api/tasks/${current.id}/runs`, { kind: "checks", revision: current.revision,
      command_id: $("check-command").value });
    trackedRuns.add(job.id);
    await loadRuns();
  });
});
$("tab-runs").addEventListener("click", () => loadRuns().catch((failure) => error(failure.message)));
$("access-form").addEventListener("submit", () => {
  clearTimeout(runtimeTimer);
  setTimeout(() => loadRuntime().catch((failure) => error(failure.message)), 250);
});
loadRuntime().catch((failure) => { if (!$("access-dialog").open) error(failure.message); });
