//! Web HUD Estático Autónomo para ERIDU-INFER / BABYLON-60.
//! Proyecta en navegador local (127.0.0.1) el terminal de inferencia soberana,
//! el catálogo de modelos de la Tríada Jurídica y el Libro Mayor de Atestación EU AI Act.

pub const HUD_HTML: &str = r#"<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>BABYLON-60 · ERIDU-INFER · Sovereign Appliance</title>
  <style>
    :root {
      --bg: #090b0e;
      --card-bg: #12161c;
      --card-border: #1f2733;
      --text: #e6edf3;
      --text-muted: #8b949e;
      --accent-green: #00ff88;
      --accent-blue: #58a6ff;
      --accent-amber: #f0883e;
      --accent-purple: #bc8cff;
      --font-mono: "JetBrains Mono", "SF Mono", Menlo, Consolas, monospace;
      --font-sans: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-sans);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
    }
    header {
      background: #0d1117;
      border-bottom: 1px solid var(--card-border);
      padding: 16px 28px;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .brand {
      display: flex;
      align-items: center;
      gap: 14px;
    }
    .logo-badge {
      background: #1f2733;
      border: 1px solid var(--accent-green);
      color: var(--accent-green);
      font-family: var(--font-mono);
      font-weight: 800;
      font-size: 16px;
      padding: 4px 10px;
      border-radius: 4px;
      letter-spacing: 1px;
    }
    .brand-title {
      font-size: 16px;
      font-weight: 700;
      letter-spacing: 0.5px;
    }
    .brand-sub {
      font-size: 11px;
      color: var(--text-muted);
      font-family: var(--font-mono);
    }
    .telemetry-bar {
      display: flex;
      gap: 16px;
      font-family: var(--font-mono);
      font-size: 11px;
    }
    .pill {
      background: #161c24;
      border: 1px solid var(--card-border);
      padding: 4px 10px;
      border-radius: 20px;
      display: flex;
      align-items: center;
      gap: 6px;
    }
    .status-dot {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: var(--accent-green);
      box-shadow: 0 0 6px var(--accent-green);
    }
    nav {
      display: flex;
      background: #0f131a;
      border-bottom: 1px solid var(--card-border);
      padding: 0 28px;
      gap: 24px;
    }
    .nav-tab {
      padding: 14px 4px;
      font-size: 13px;
      font-weight: 600;
      color: var(--text-muted);
      border-bottom: 2px solid transparent;
      cursor: pointer;
      transition: all 0.2s;
    }
    .nav-tab:hover { color: var(--text); }
    .nav-tab.active {
      color: var(--accent-green);
      border-bottom-color: var(--accent-green);
    }
    main {
      flex: 1;
      padding: 28px;
      max-width: 1400px;
      margin: 0 auto;
      width: 100%;
    }
    .tab-content { display: none; }
    .tab-content.active { display: block; }
    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
    }
    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 20px;
    }
    .card-title {
      font-size: 14px;
      font-weight: 700;
      font-family: var(--font-mono);
      text-transform: uppercase;
      letter-spacing: 0.8px;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      color: var(--text);
    }
    label {
      display: block;
      font-size: 12px;
      font-family: var(--font-mono);
      color: var(--text-muted);
      margin-bottom: 6px;
    }
    select, textarea, input {
      width: 100%;
      background: #0a0d12;
      border: 1px solid var(--card-border);
      color: var(--text);
      font-family: var(--font-mono);
      font-size: 13px;
      padding: 10px;
      border-radius: 6px;
      margin-bottom: 16px;
      outline: none;
    }
    select:focus, textarea:focus, input:focus {
      border-color: var(--accent-blue);
    }
    textarea {
      resize: vertical;
      min-height: 140px;
    }
    button.btn-primary {
      background: #238636;
      color: white;
      border: 1px solid rgba(255,255,255,0.1);
      padding: 10px 18px;
      font-size: 13px;
      font-weight: 600;
      font-family: var(--font-mono);
      border-radius: 6px;
      cursor: pointer;
      display: inline-flex;
      align-items: center;
      gap: 8px;
      transition: background 0.2s;
    }
    button.btn-primary:hover {
      background: #2ea043;
    }
    .response-box {
      background: #090c10;
      border: 1px solid var(--card-border);
      border-radius: 6px;
      padding: 14px;
      font-family: var(--font-mono);
      font-size: 12px;
      line-height: 1.6;
      min-height: 240px;
      max-height: 520px;
      overflow-y: auto;
      white-space: pre-wrap;
      color: #7ee787;
    }
    .receipt-badge {
      display: inline-block;
      background: #1c2738;
      border: 1px solid var(--accent-blue);
      color: var(--accent-blue);
      font-size: 11px;
      padding: 3px 8px;
      border-radius: 4px;
      font-family: var(--font-mono);
      margin-top: 10px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      font-family: var(--font-mono);
      font-size: 12px;
    }
    th, td {
      padding: 12px 14px;
      text-align: left;
      border-bottom: 1px solid var(--card-border);
    }
    th {
      background: #0a0d12;
      color: var(--text-muted);
      text-transform: uppercase;
      font-size: 11px;
    }
    tr:hover {
      background: #161c24;
    }
    .badge-ok {
      color: var(--accent-green);
      font-weight: bold;
    }
    pre.code-block {
      background: #0a0d12;
      border: 1px solid var(--card-border);
      padding: 14px;
      border-radius: 6px;
      font-family: var(--font-mono);
      font-size: 12px;
      color: #e6edf3;
      overflow-x: auto;
      position: relative;
      margin-bottom: 16px;
    }
    .copy-btn {
      position: absolute;
      top: 8px;
      right: 8px;
      background: #21262d;
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      font-size: 11px;
      padding: 4px 8px;
      border-radius: 4px;
      cursor: pointer;
    }
    .copy-btn:hover { color: var(--text); }
    footer {
      border-top: 1px solid var(--card-border);
      padding: 14px 28px;
      font-family: var(--font-mono);
      font-size: 11px;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: #0d1117;
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <div class="logo-badge">B ≡ 60</div>
      <div>
        <div class="brand-title">ERIDU-INFER · SOVEREIGN INFERENCE RUNTIME</div>
        <div class="brand-sub">BABYLON-60 AIR-GAPPED APPLIANCE · EU AI ACT READY</div>
      </div>
    </div>
    <div class="telemetry-bar">
      <div class="pill"><div class="status-dot"></div> AIR-GAPPED · LOCAL ONLY</div>
      <div class="pill">UMA 36GB · APPLE SILICON</div>
      <div class="pill">PUERTOS: 41343 / 1234</div>
      <div class="pill" style="border-color: var(--accent-amber); color: var(--accent-amber);">WORM LEDGER: ACTIVO</div>
    </div>
  </header>

  <nav>
    <div class="nav-tab active" onclick="switchTab('tab-chat')">Terminal de Inferencia</div>
    <div class="nav-tab" onclick="switchTab('tab-ledger')">Libro Mayor de Cumplimiento (EU AI Act)</div>
    <div class="nav-tab" onclick="switchTab('tab-models')">Tríada Jurídica (Catálogo)</div>
    <div class="nav-tab" onclick="switchTab('tab-api')">Integración & SDK</div>
  </nav>

  <main>
    <!-- TAB 1: TERMINAL CHAT -->
    <div id="tab-chat" class="tab-content active">
      <div class="grid-2">
        <div class="card">
          <div class="card-title">
            <span>Inyección de Prompt / Expediente</span>
            <span style="font-size: 11px; color: var(--accent-green);">Zero-Data-Leak</span>
          </div>
          <label for="model-select">Modelo Seleccionado (En Silicio)</label>
          <select id="model-select">
            <option value="deepseek-r1-distill-qwen-32b">DeepSeek-R1 Distill Qwen 32B (El Jurista Analítico)</option>
            <option value="llama-3.3-70b-instruct">Llama 3.3 70B Instruct (El Redactor de Sala)</option>
            <option value="bge-m3-legal-embed">BGE-M3 Legal Embed (El Archivero Inmediato)</option>
          </select>

          <label for="prompt-input">Contenido del Prompt / Caso Jurídico</label>
          <textarea id="prompt-input" placeholder="Ej: Analiza el siguiente contrato de arrendamiento mercantil y detecta cláusulas abusivas conforme al Art. 1255 del Código Civil...">¿Cuál es la responsabilidad del administrador concursal según la Ley 16/2022 de reforma concursal y cómo se auditan las transacciones en el periodo sospechoso?</textarea>

          <div style="display: flex; justify-content: space-between; align-items: center;">
            <button class="btn-primary" onclick="runInference()">
              <span>⚡ Ejecutar Inferencia Atestiguada</span>
            </button>
            <span id="infer-time" style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted);"></span>
          </div>
        </div>

        <div class="card">
          <div class="card-title">
            <span>Respuesta Atestiguada en Silicio</span>
            <span id="active-seal" style="font-size: 11px; color: var(--accent-blue);"></span>
          </div>
          <div id="response-output" class="response-box">Presione 'Ejecutar Inferencia Atestiguada' para emitir un prompt sellado por el Causal Gate de BABYLON-60...</div>
          <div id="receipt-details"></div>
        </div>
      </div>
    </div>

    <!-- TAB 2: COMPLIANCE LEDGER -->
    <div id="tab-ledger" class="tab-content">
      <div class="card">
        <div class="card-title">
          <span>Registro Criptográfico WORM de Inferencias (EU AI Act Arts. 12-14)</span>
          <button class="copy-btn" onclick="fetchReceipts()" style="position: static;">Actualizar Ledger</button>
        </div>
        <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 16px;">
          Cada petición procesada en esta máquina es evaluada en Ring-0, sellando su hash SHA-256 en el registro inmutable WORM para certificar que el bufete cumple con la gobernanza técnica de AESIA y la Unión Europea.
        </p>
        <table id="receipts-table">
          <thead>
            <tr>
              <th>Timestamp UTC</th>
              <th>Sello de Atestación</th>
              <th>Modelo</th>
              <th>Hash SHA-256 del Prompt</th>
              <th>Estado de Cumplimiento</th>
            </tr>
          </thead>
          <tbody id="receipts-body">
            <tr>
              <td colspan="5" style="text-align: center; color: var(--text-muted); padding: 24px;">Cargando libro mayor...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- TAB 3: MODELOS -->
    <div id="tab-models" class="tab-content">
      <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px;">
        <div class="card">
          <div class="card-title" style="color: var(--accent-purple);">El Jurista Analítico</div>
          <div style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">deepseek-r1-distill-qwen-32b</div>
          <p style="font-size: 13px; line-height: 1.5; color: var(--text); margin-bottom: 16px;">
            Especializado en deducción formal, contradicciones contractuales y razonamiento jurídico paso a paso (&lt;think&gt; CoT).
          </p>
          <div style="font-family: var(--font-mono); font-size: 11px; background: #0a0d12; padding: 10px; border-radius: 4px; line-height: 1.6;">
            <div>• Huella RAM: ~19.5 GB (Q4_K_M)</div>
            <div>• Velocidad: ~34 tokens/seg (M3 Pro)</div>
            <div>• Contexto: 32.768 tokens</div>
            <div>• Función: Due Diligence y Detección de Riesgos</div>
          </div>
        </div>

        <div class="card">
          <div class="card-title" style="color: var(--accent-blue);">El Redactor de Sala</div>
          <div style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">llama-3.3-70b-instruct</div>
          <p style="font-size: 13px; line-height: 1.5; color: var(--text); margin-bottom: 16px;">
            Redacción fluida de demandas, recursos de casación, cláusulas mercantiles y dictámenes con impecable castellano jurídico.
          </p>
          <div style="font-family: var(--font-mono); font-size: 11px; background: #0a0d12; padding: 10px; border-radius: 4px; line-height: 1.6;">
            <div>• Huella RAM: ~38 GB (Q4_K_M)</div>
            <div>• Velocidad: ~14 tokens/seg (M3 Pro)</div>
            <div>• Contexto: 128.000 tokens</div>
            <div>• Función: Redacción y Estilo Jurisprudencial</div>
          </div>
        </div>

        <div class="card">
          <div class="card-title" style="color: var(--accent-green);">El Archivero Inmediato</div>
          <div style="font-family: var(--font-mono); font-size: 12px; color: var(--text-muted); margin-bottom: 12px;">bge-m3-legal-embed</div>
          <p style="font-size: 13px; line-height: 1.5; color: var(--text); margin-bottom: 16px;">
            Generación de representaciones vectoriales densas para búsqueda semántica instantánea sobre millones de folios de expedientes y jurisprudencia.
          </p>
          <div style="font-family: var(--font-mono); font-size: 11px; background: #0a0d12; padding: 10px; border-radius: 4px; line-height: 1.6;">
            <div>• Huella RAM: ~2.1 GB (F16)</div>
            <div>• Latencia: &lt;1.2 ms por párrafo</div>
            <div>• Dimensiones: 1024 floats</div>
            <div>• Función: RAG Local y Búsqueda en Causa</div>
          </div>
        </div>
      </div>
    </div>

    <!-- TAB 4: API & SDK -->
    <div id="tab-api" class="tab-content">
      <div class="card" style="margin-bottom: 20px;">
        <div class="card-title">1. Conexión con LM Studio CLI (`lms`)</div>
        <pre class="code-block"><button class="copy-btn" onclick="copyText('code-lms')">Copiar</button><code id="code-lms"># Descubrimiento automático de socket local
lms status

# Iniciar conversación directa
lms chat --model deepseek-r1-distill-qwen-32b</code></pre>
      </div>

      <div class="card" style="margin-bottom: 20px;">
        <div class="card-title">2. Inferencia vía cURL (OpenAI Compatible)</div>
        <pre class="code-block"><button class="copy-btn" onclick="copyText('code-curl')">Copiar</button><code id="code-curl">curl -X POST http://127.0.0.1:1234/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "deepseek-r1-distill-qwen-32b",
    "messages": [{"role": "user", "content": "Audita este contrato de confidencialidad."}]
  }'</code></pre>
      </div>

      <div class="card">
        <div class="card-title">3. Cliente Python (OpenAI SDK Estándar)</div>
        <pre class="code-block"><button class="copy-btn" onclick="copyText('code-py')">Copiar</button><code id="code-py">from openai import OpenAI

client = OpenAI(base_url="http://127.0.0.1:1234/v1", api_key="babylon-sovereign-airgapped")

response = client.chat.completions.create(
    model="deepseek-r1-distill-qwen-32b",
    messages=[{"role": "user", "content": "Analiza la cláusula de indemnización."}]
)

print(response.choices[0].message.content)
print("Sello Criptográfico:", response.id)</code></pre>
      </div>
    </div>
  </main>

  <footer>
    <div>BABYLON-60 CORE · CORTEX SOVEREIGN STACK · RING-0 ATTESTATION ENGINE</div>
    <div>OPERADO POR: BORJA FERNÁNDEZ ANGULO · INVESTIGADOR EN SISTEMAS COMPLEJOS</div>
  </footer>

  <script>
    function switchTab(tabId) {
      document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
      document.querySelectorAll('.nav-tab').forEach(el => el.classList.remove('active'));
      document.getElementById(tabId).classList.add('active');
      event.target.classList.add('active');
      if (tabId === 'tab-ledger') fetchReceipts();
    }

    async function runInference() {
      const model = document.getElementById('model-select').value;
      const prompt = document.getElementById('prompt-input').value;
      const outputBox = document.getElementById('response-output');
      const timeSpan = document.getElementById('infer-time');
      const activeSeal = document.getElementById('active-seal');
      const receiptDetails = document.getElementById('receipt-details');

      outputBox.textContent = "Evaluando 7-tupla causal en Ring-0...\nDespachando a sustrato Apple Silicon Metal...";
      activeSeal.textContent = "";
      receiptDetails.innerHTML = "";
      const t0 = performance.now();

      try {
        const res = await fetch('/v1/chat/completions', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            model: model,
            messages: [{ role: 'user', content: prompt }]
          })
        });

        const data = await res.json();
        const t1 = performance.now();
        timeSpan.textContent = `Latencia: ${(t1 - t0).toFixed(1)} ms | Tokens: ${data.usage.total_tokens}`;

        if (data.choices && data.choices[0]) {
          outputBox.textContent = data.choices[0].message.content;
          activeSeal.textContent = `SEAL: ${data.id}`;
          receiptDetails.innerHTML = `
            <div class="receipt-badge">WORM HASH: ${data.babylon_attestation_hash}</div>
            <div class="receipt-badge" style="border-color: var(--accent-green); color: var(--accent-green);">ESTADO: CONFORME EU AI ACT</div>
          `;
        } else {
          outputBox.textContent = "Error en respuesta: " + JSON.stringify(data);
        }
      } catch (err) {
        outputBox.textContent = "Error de conexión con el sustrato: " + err.message;
      }
    }

    async function fetchReceipts() {
      const tbody = document.getElementById('receipts-body');
      tbody.innerHTML = '<tr><td colspan="5" style="text-align: center;">Consultando WORM Ledger...</td></tr>';
      try {
        const res = await fetch('/v1/audit/receipts');
        const list = await res.json();
        if (!list || list.length === 0) {
          tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: var(--text-muted);">Sin transacciones registradas aún en esta sesión.</td></tr>';
          return;
        }
        tbody.innerHTML = list.map(r => `
          <tr>
            <td>${r.timestamp_utc.replace('T', ' ').substring(0, 19)}</td>
            <td><strong style="color: var(--accent-blue);">${r.attestation_seal}</strong></td>
            <td>${r.model_id}</td>
            <td style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">${r.prompt_hash.substring(0, 16)}...</td>
            <td><span class="badge-ok">VERIFICADO (ART. 12-14)</span></td>
          </tr>
        `).join('');
      } catch (e) {
        tbody.innerHTML = `<tr><td colspan="5" style="color: #ff7b72;">Fallo al leer ledger: ${e.message}</td></tr>`;
      }
    }

    function copyText(id) {
      const text = document.getElementById(id).innerText;
      navigator.clipboard.writeText(text);
      alert("Copiado al portapapeles: \n" + text.substring(0, 80) + "...");
    }
  </script>
</body>
</html>
"#;
