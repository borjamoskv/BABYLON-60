(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))s(n);new MutationObserver(n=>{for(const r of n)if(r.type==="childList")for(const f of r.addedNodes)f.tagName==="LINK"&&f.rel==="modulepreload"&&s(f)}).observe(document,{childList:!0,subtree:!0});function a(n){const r={};return n.integrity&&(r.integrity=n.integrity),n.referrerPolicy&&(r.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?r.credentials="include":n.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function s(n){if(n.ep)return;n.ep=!0;const r=a(n);fetch(n.href,r)}})();const M="";async function h(t){const e=await fetch(`${M}${t}`);if(!e.ok){const a=await e.json().catch(()=>({detail:e.statusText}));throw new Error(a.detail||e.statusText)}return e.json()}async function k(t,e){const a=await fetch(`${M}${t}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok){const s=await a.json().catch(()=>({detail:a.statusText}));throw new Error(s.detail||a.statusText)}return a.json()}function O(t,e,a){const s=location.protocol==="https:"?"wss:":"ws:",n=new WebSocket(`${s}//${location.host}${t}`);return n.onmessage=r=>e(JSON.parse(r.data)),n.onerror=r=>a==null?void 0:a(r),n.onclose=()=>{setTimeout(()=>O(t,e,a),3e3)},n}const C={};let S=null;function T(t,e){C[t]=e}function I(t){if(S===t)return;S=t,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===t)});const e=document.getElementById("main-content");C[t]&&(e.innerHTML="",C[t](e)),history.replaceState(null,"",`#${t}`)}function H(){const t=location.hash.replace("#","");return t&&C[t]?t:"ledger"}let N=[],x=null,L=null;document.addEventListener("DOMContentLoaded",async()=>{R(),_(),await q();const t=H();I(t)});async function q(){try{N=await h("/api/databases");const t=document.querySelector(".db-count .count");t&&(t.textContent=N.length)}catch(t){console.error("Failed to fetch databases:",t)}}function R(){const t=document.getElementById("sidebar");t.innerHTML=`
    <div class="sidebar-header">
      <div class="sidebar-logo">
        <div class="dot"></div>
        BABYLON·60
      </div>
      <div class="sidebar-subtitle">SOVEREIGN AGENT MEMORY</div>
      <div class="sidebar-status">
        <div class="status-indicator"></div>
        <span class="status-text">CONNECTED</span>
      </div>
    </div>
    <div class="sidebar-nav">
      <div class="nav-section-label">INSPECTOR</div>
      <div class="nav-item" data-route="ledger">
        <span class="icon">⧉</span>
        <span>BFT Ledger</span>
        <span class="shortcut">⌘1</span>
      </div>
      <div class="nav-item" data-route="databases">
        <span class="icon">⛁</span>
        <span>Ontologies</span>
        <span class="shortcut">⌘2</span>
      </div>
      <div class="nav-section-label">ANALYSIS</div>
      <div class="nav-item" data-route="query">
        <span class="icon">❯_</span>
        <span>SQL Console</span>
        <span class="shortcut">⌘3</span>
      </div>
      <div class="nav-item" data-route="telemetry">
        <span class="icon">⚡</span>
        <span>Telemetry</span>
        <span class="shortcut">⌘4</span>
      </div>
    </div>
    <div class="sidebar-footer">
      <div class="db-count">
        Databases: <span class="count">0</span>
      </div>
      <div style="margin-top: 4px; opacity: 0.5;">MOSKV-1 APEX v1.0.2</div>
    </div>
  `,t.querySelectorAll(".nav-item").forEach(e=>{e.addEventListener("click",()=>{I(e.dataset.route)})}),window.addEventListener("keydown",e=>{(e.metaKey||e.ctrlKey)&&["1","2","3","4"].includes(e.key)&&(e.preventDefault(),I(["ledger","databases","query","telemetry"][parseInt(e.key)-1]))})}function w(t,e){const a=document.querySelector(".status-indicator"),s=document.querySelector(".status-text");!a||!s||(a.className="status-indicator",t==="error"?a.classList.add("error"):t==="loading"&&a.classList.add("loading"),s.textContent=e.toUpperCase())}function _(){T("ledger",P),T("databases",z),T("query",F),T("telemetry",j),window.addEventListener("hashchange",()=>{const t=window.location.hash.replace("#","");t&&I(t)})}function D(t,e){L&&L.remove();const a=document.createElement("div");a.className="tooltip fade-in",a.innerHTML=e,document.body.appendChild(a),L=a;const s=t.target.getBoundingClientRect();a.style.left=`${s.left+window.scrollX+20}px`,a.style.top=`${s.top+window.scrollY-10}px`}function A(){L&&(L.remove(),L=null)}async function P(t){t.innerHTML=`
    <div class="panel-header slide-in">
      <div class="panel-title">BFT MASTER LEDGER</div>
      <div class="panel-badge live">ACTIVE</div>
    </div>
    <div class="panel-body slide-in">
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Ledger File</div>
          <div class="stat-value lapis" id="stat-db-name">-</div>
          <div class="stat-sub">SQLite storage</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Total Entries</div>
          <div class="stat-value gold" id="stat-total-entries">0</div>
          <div class="stat-sub" id="stat-latest-time">-</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Consensus State</div>
          <div class="stat-value verify" id="stat-integrity">UNKNOWN</div>
          <div class="stat-sub" id="stat-latest-lamport">Lamport: -</div>
        </div>
      </div>

      <div class="card" style="margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div class="card-title">Cryptographic Hash Chain Verification</div>
          <button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Integrity</button>
        </div>
        <div class="verify-progress" style="display: none;">
          <div class="verify-progress-bar"></div>
        </div>
        <div class="chain-container" id="chain-visual-grid">
          <div class="empty-state" style="padding: 20px 0;">
            <div class="icon">⚿</div>
            <div class="desc">Execute verification to map blocks and assert consensus state.</div>
          </div>
        </div>
      </div>

      <div class="card">
        <div class="card-title" style="margin-bottom: 12px;">Ledger Sequence</div>
        <div style="overflow-x: auto;">
          <table class="data-table">
            <thead>
              <tr>
                <th>Seq</th>
                <th>Stream</th>
                <th>Event Type</th>
                <th>Lamport T</th>
                <th>Taint Provenance</th>
                <th>Timestamp</th>
                <th>Entry Hash</th>
              </tr>
            </thead>
            <tbody id="ledger-table-body">
              <tr>
                <td colspan="7" class="empty-state" style="text-align: center;">Loading ledger entries...</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination">
          <button class="btn" id="btn-ledger-prev" disabled>◀ Prev</button>
          <span style="font-family: var(--font-mono); font-size: 0.75rem;" id="ledger-page-info">Page 1</span>
          <button class="btn" id="btn-ledger-next" disabled>Next ▶</button>
        </div>
      </div>
    </div>

    <!-- Details Sidebar Overlay -->
    <div id="entry-detail-panel" class="card" style="display: none; position: fixed; top: var(--header-height); right: 0; width: 450px; height: calc(100vh - var(--header-height)); border-radius: 0; border-left: 1px solid var(--edge); z-index: 10; display: flex; flex-direction: column; background: var(--kiln); transform: translateX(100%); transition: transform var(--transition-normal);">
      <div style="display: flex; justify-content: space-between; align-items: center; padding: 16px; border-bottom: 1px solid var(--edge);">
        <div class="card-title" id="detail-title" style="margin-bottom: 0;">Entry #0</div>
        <button class="btn" id="btn-close-detail" style="padding: 2px 8px;">✕</button>
      </div>
      <div style="flex: 1; overflow-y: auto; padding: 16px; font-family: var(--font-mono); font-size: 0.75rem;">
        <div style="margin-bottom: 14px;">
          <div class="stat-label">Event UUID</div>
          <div id="detail-uuid" style="color: var(--dust); word-break: break-all; margin-top: 4px;">-</div>
        </div>
        <div style="margin-bottom: 14px;">
          <div class="stat-label">Cortex Taint Signature</div>
          <div id="detail-taint" style="color: var(--lapis-bright); word-break: break-all; margin-top: 4px;">-</div>
        </div>
        <div style="margin-bottom: 14px;">
          <div class="stat-label">Linkages</div>
          <div style="margin-top: 4px;">Prev: <span id="detail-prev-hash" style="color: var(--dust-dim);">-</span></div>
          <div style="margin-top: 2px;">Curr: <span id="detail-curr-hash" style="color: var(--verify);">-</span></div>
        </div>
        <div>
          <div class="stat-label" style="margin-bottom: 6px;">Payload State</div>
          <pre id="detail-payload" style="background: var(--tablet); border: 1px solid var(--edge); padding: 10px; border-radius: var(--radius-sm); color: var(--dust-dim); overflow-x: auto; font-family: var(--font-mono); line-height: 1.5;"></pre>
        </div>
      </div>
    </div>
  `;let e=50,a=0;const s=async()=>{try{const l=await h("/api/ledger/stats");l.exists?(document.getElementById("stat-db-name").textContent=l.db_path,document.getElementById("stat-total-entries").textContent=l.entries,l.latest&&l.latest.created_at&&(document.getElementById("stat-latest-time").textContent=l.latest.created_at,document.getElementById("stat-latest-lamport").textContent=`Lamport: t=${l.latest.lamport_t}`)):(document.getElementById("stat-db-name").textContent="NOT FOUND",document.getElementById("stat-integrity").textContent="NO LEDGER",document.getElementById("stat-integrity").className="stat-value break")}catch(l){console.error(l)}},n=async()=>{try{const l=await h(`/api/ledger/entries?limit=${e}&offset=${a}`),i=document.getElementById("ledger-table-body");if(i.innerHTML="",!l.entries||l.entries.length===0){i.innerHTML='<tr><td colspan="7" class="empty-state">No entries in this ledger database yet.</td></tr>';return}l.entries.forEach(o=>{const d=document.createElement("tr");d.style.cursor="pointer",d.innerHTML=`
          <td class="seq-cell">#${o.seq}</td>
          <td class="stream-cell">${v(o.stream)}</td>
          <td style="color: var(--dust); font-weight: 500;">${v(o.event_type)}</td>
          <td>${o.lamport_t}</td>
          <td style="font-size: 0.65rem; color: var(--dust-faint); max-width: 150px; overflow: hidden; text-overflow: ellipsis;">
            ${v(o.cortex_taint||"None")}
          </td>
          <td class="time-cell">${o.created_at}</td>
          <td class="hash-cell">${o.entry_hash.slice(0,16)}...</td>
        `,d.addEventListener("click",()=>r(o.seq)),i.appendChild(d)}),document.getElementById("btn-ledger-prev").disabled=a===0,document.getElementById("btn-ledger-next").disabled=a+e>=l.total,document.getElementById("ledger-page-info").textContent=`Showing ${a+1} - ${Math.min(a+e,l.total)} of ${l.total}`}catch(l){console.error(l)}},r=async l=>{try{const i=await h(`/api/ledger/entry/${l}`),o=document.getElementById("entry-detail-panel");document.getElementById("detail-title").textContent=`Ledger Entry #${i.seq}`,document.getElementById("detail-uuid").textContent=i.event_id,document.getElementById("detail-taint").textContent=i.cortex_taint||"None",document.getElementById("detail-prev-hash").textContent=i.prev_hash,document.getElementById("detail-curr-hash").textContent=i.entry_hash;let d={};try{d=JSON.parse(i.payload_json)}catch{d=i.payload_json}document.getElementById("detail-payload").textContent=JSON.stringify(d,null,2),o.style.display="flex",o.offsetWidth,o.style.transform="translateX(0)"}catch(i){alert(`Failed to load entry details: ${i.message}`)}},f=()=>{const l=document.getElementById("entry-detail-panel");l.style.transform="translateX(100%)",setTimeout(()=>{l.style.display="none"},220)},b=async()=>{const l=document.getElementById("btn-verify-chain"),i=document.querySelector(".verify-progress"),o=document.querySelector(".verify-progress-bar"),d=document.getElementById("chain-visual-grid");l.disabled=!0,i.style.display="block",o.style.width="20%",w("loading","VERIFYING CHAIN");try{o.style.width="60%";const c=await k("/api/ledger/verify");if(o.style.width="100%",d.innerHTML="",!c.entries||c.entries.length===0){d.innerHTML='<div class="empty-state"><div class="desc">No verified entries.</div></div>';return}c.entries.forEach(y=>{const p=document.createElement("div");p.className=`chain-block ${y.valid?"":"invalid"}`,p.addEventListener("mouseenter",u=>{const g=y.valid?'<span style="color: var(--verify);">VALID linkage</span>':`<span style="color: var(--break); font-weight:700;">BROKEN: ${y.errors.join(", ")}</span>`;D(u,`
            <strong>Sequence #${y.seq}</strong><br/>
            Stream: ${v(y.stream)}<br/>
            Lamport T: ${y.lamport_t}<br/>
            Hash: <span style="font-family: var(--font-mono);">${y.entry_hash}</span><br/>
            Status: ${g}
          `)}),p.addEventListener("mouseleave",A),p.addEventListener("click",()=>r(y.seq)),d.appendChild(p)});const m=document.getElementById("stat-integrity");c.valid?(m.textContent="INTEGRITY OK",m.className="stat-value verify",w("connected","CONNECTED")):(m.textContent=`COMPROMISED (Seq #${c.broken_at})`,m.className="stat-value break",w("error","LEDGER BROKEN"))}catch(c){d.innerHTML=`<div class="empty-state"><div class="icon">⚠</div><div class="desc" style="color: var(--break);">${v(c.message)}</div></div>`,w("error","ERROR")}finally{l.disabled=!1,setTimeout(()=>{i.style.display="none"},600)}};document.getElementById("btn-ledger-prev").addEventListener("click",()=>{a>=e&&(a-=e,n())}),document.getElementById("btn-ledger-next").addEventListener("click",()=>{a+=e,n()}),document.getElementById("btn-verify-chain").addEventListener("click",b),document.getElementById("btn-close-detail").addEventListener("click",f),await s(),await n()}async function z(t){t.innerHTML=`
    <div class="panel-header slide-in">
      <div class="panel-title">ONTOLOGY DATABASE EXPLORER</div>
      <div class="panel-badge beta">EXPLORER</div>
    </div>
    <div class="panel-body slide-in" style="display: flex; gap: 20px; overflow: hidden; height: calc(100% - var(--header-height));">
      
      <!-- Left sidebar: database file tree -->
      <div class="card" style="width: 280px; min-width: 280px; display: flex; flex-direction: column; overflow-y: auto;">
        <div class="card-title">Discovered Files</div>
        <div id="db-tree-container" class="tree-node" style="padding-left: 0;">
          <div class="loading-text">Loading workspace directories...</div>
        </div>
      </div>

      <!-- Right main view: table preview -->
      <div style="flex: 1; display: flex; flex-direction: column; gap: 20px; overflow: hidden;">
        
        <!-- Schema section -->
        <div class="card" id="db-schema-card" style="display: none; flex-direction: column; max-height: 200px;">
          <div class="card-title" id="schema-card-title">Schema Information</div>
          <div style="flex: 1; overflow-y: auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>CID</th>
                  <th>Name</th>
                  <th>Type</th>
                  <th>NotNull</th>
                  <th>Default</th>
                  <th>PK</th>
                </tr>
              </thead>
              <tbody id="schema-table-body"></tbody>
            </table>
          </div>
        </div>

        <!-- Row browser section -->
        <div class="card" id="db-rows-card" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;">
          <div class="card-title" id="rows-card-title">Table Browser</div>
          <div style="flex: 1; overflow: auto;" id="table-rows-container">
            <div class="empty-state">
              <div class="icon">⛁</div>
              <div class="desc">Select a database and table from the tree on the left to inspect records.</div>
            </div>
          </div>
          <div class="pagination" id="rows-pagination" style="display: none; border-top: 1px solid var(--edge); margin-top: auto;">
            <button class="btn" id="btn-rows-prev" disabled>◀ Prev</button>
            <span style="font-family: var(--font-mono); font-size: 0.75rem;" id="rows-page-info">Page 1</span>
            <button class="btn" id="btn-rows-next" disabled>Next ▶</button>
          </div>
        </div>
      </div>

    </div>
  `;let e=null,a=null,s=50,n=0;const r=async()=>{const i=document.getElementById("db-tree-container");try{const o=await h("/api/databases");if(i.innerHTML="",o.length===0){i.innerHTML='<div class="empty-state" style="padding: 10px 0;"><div class="desc">No databases found.</div></div>';return}o.forEach(d=>{const c=document.createElement("div");c.className="tree-item",c.innerHTML=`<span class="tree-icon">⛁</span><span>${v(d.name)}</span><span class="tree-count">${d.size_human}</span>`;const m=document.createElement("div");m.className="tree-node",m.style.display="none",c.addEventListener("click",async()=>{const y=m.style.display==="none";if(i.querySelectorAll(".tree-node").forEach(p=>p.style.display="none"),i.querySelectorAll(".tree-item").forEach(p=>p.classList.remove("active")),y&&(c.classList.add("active"),m.style.display="block",m.innerHTML==="")){m.innerHTML='<div style="padding: 4px 16px; opacity:0.5; font-size:0.7rem;">Querying tables...</div>';try{const p=await h(`/api/databases/${d.name}/tables`);m.innerHTML="",p.forEach(u=>{const g=document.createElement("div");g.className="tree-item",g.style.paddingLeft="8px",g.innerHTML=`<span class="tree-icon">▤</span><span>${v(u.name)}</span><span class="tree-count">${u.row_count}</span>`,g.addEventListener("click",B=>{B.stopPropagation(),m.querySelectorAll(".tree-item").forEach(E=>E.classList.remove("active")),g.classList.add("active"),f(d.name,u.name)}),m.appendChild(g)})}catch(p){m.innerHTML=`<div style="padding:4px 16px; color:var(--break); font-size:0.7rem;">${v(p.message)}</div>`}}}),i.appendChild(c),i.appendChild(m)})}catch(o){i.innerHTML=`<div style="color:var(--break); font-size:0.75rem; padding: 10px;">${v(o.message)}</div>`}},f=async(i,o)=>{e=i,a=o,n=0,document.getElementById("db-schema-card").style.display="flex",document.getElementById("schema-card-title").textContent=`SCHEMA — ${i}.${o}`,document.getElementById("rows-card-title").textContent=`RECORDS — ${i}.${o}`,await b(),await l()},b=async()=>{const i=document.getElementById("schema-table-body");i.innerHTML='<tr><td colspan="6" style="text-align:center; opacity:0.5;">Loading schema...</td></tr>';try{const o=await h(`/api/databases/${e}/schema/${a}`);i.innerHTML="",o.forEach(d=>{const c=document.createElement("tr");c.innerHTML=`
          <td>${d.cid}</td>
          <td style="color: var(--dust); font-weight:600;">${v(d.name)}</td>
          <td style="color: var(--lapis-bright);">${v(d.type)}</td>
          <td>${d.notnull?"YES":"NO"}</td>
          <td>${d.default!==null?v(String(d.default)):"NULL"}</td>
          <td style="color: ${d.pk?"var(--gold)":"var(--dust-ghost)"}; font-weight: 700;">${d.pk?"PRIMARY KEY":"-"}</td>
        `,i.appendChild(c)})}catch(o){i.innerHTML=`<tr><td colspan="6" style="color:var(--break); text-align:center;">${v(o.message)}</td></tr>`}},l=async()=>{const i=document.getElementById("table-rows-container"),o=document.getElementById("rows-pagination");i.innerHTML='<div style="text-align:center; padding: 30px; opacity:0.5;">Querying records...</div>',o.style.display="none";try{const d=await h(`/api/databases/${e}/tables/${a}?limit=${s}&offset=${n}`);if(i.innerHTML="",d.rows.length===0){i.innerHTML='<div class="empty-state"><div class="desc">No rows found in this table.</div></div>';return}const c=document.createElement("table");c.className="data-table";const m=document.createElement("thead"),y=document.createElement("tr");d.columns.forEach(u=>{y.innerHTML+=`<th>${v(u)}</th>`}),m.appendChild(y),c.appendChild(m);const p=document.createElement("tbody");d.rows.forEach(u=>{const g=document.createElement("tr");d.columns.forEach(B=>{const E=u[B];let $=E===null?'<span style="opacity:0.3;">NULL</span>':v(String(E));typeof E=="string"&&E.length>120&&($=`<span title="${v(E)}">${v(E.slice(0,120))}...</span>`),g.innerHTML+=`<td>${$}</td>`}),p.appendChild(g)}),c.appendChild(p),i.appendChild(c),o.style.display="flex",document.getElementById("btn-rows-prev").disabled=n===0,document.getElementById("btn-rows-next").disabled=n+s>=d.total,document.getElementById("rows-page-info").textContent=`Showing ${n+1} - ${Math.min(n+s,d.total)} of ${d.total}`}catch(d){i.innerHTML=`<div style="color:var(--break); padding:30px; text-align:center;">${v(d.message)}</div>`}};document.getElementById("btn-rows-prev").addEventListener("click",()=>{n>=s&&(n-=s,l())}),document.getElementById("btn-rows-next").addEventListener("click",()=>{n+=s,l()}),await r()}async function F(t){t.innerHTML=`
    <div class="panel-header slide-in">
      <div class="panel-title">SQL READ-ONLY CONSOLE</div>
      <div class="panel-badge beta">SANDBOX</div>
    </div>
    <div class="panel-body slide-in" style="display: flex; flex-direction: column; gap: 20px; overflow: hidden; height: calc(100% - var(--header-height));">
      
      <!-- Control / Editor card -->
      <div class="card" style="display: flex; flex-direction: column; gap: 12px; min-height: 250px;">
        <div style="display: flex; align-items: center; gap: 12px;">
          <div class="card-title" style="margin-bottom: 0;">Query Console</div>
          <select class="select" id="query-db-select" style="min-width: 200px;">
            <option value="">Select target database...</option>
          </select>
        </div>

        <div class="code-editor" style="flex: 1; display: flex; flex-direction: column;">
          <textarea id="query-sql-text" placeholder="SELECT * FROM ledger_entries ORDER BY seq DESC LIMIT 10;" spellcheck="false"></textarea>
          <div class="code-editor-toolbar">
            <span style="font-size:0.6rem; color:var(--dust-faint); letter-spacing:0.04em;">READ-ONLY ENFORCED (MUTATIONS BLOCKED)</span>
            <button class="btn btn-primary" id="btn-run-query">⚡ Run Query</button>
          </div>
        </div>
      </div>

      <!-- Results Card -->
      <div class="card" style="flex: 1; display: flex; flex-direction: column; overflow: hidden;" id="query-results-card">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
          <div class="card-title" style="margin-bottom: 0;">Output Console</div>
          <div style="font-size: 0.65rem; color: var(--dust-faint);" id="query-meta">-</div>
        </div>
        <div style="flex: 1; overflow: auto;" id="query-output-container">
          <div class="empty-state">
            <div class="icon">❯_</div>
            <div class="desc">Enter SQL query and click Run to display output schema and records.</div>
          </div>
        </div>
      </div>

    </div>
  `;const e=document.getElementById("query-db-select");try{const s=await h("/api/databases");s.forEach(n=>{const r=document.createElement("option");r.value=n.name,r.textContent=`${n.name} (${n.size_human})`,e.appendChild(r)}),s.length>0&&(e.value=s[0].name)}catch(s){console.error(s)}const a=async()=>{const s=e.value,n=document.getElementById("query-sql-text").value.trim(),r=document.getElementById("query-output-container"),f=document.getElementById("query-meta"),b=document.getElementById("btn-run-query");if(!s){alert("Please select a target database.");return}if(!n){alert("Please enter a SQL statement.");return}b.disabled=!0,r.innerHTML='<div style="text-align:center; padding: 40px; opacity:0.5;">Executing transaction against read-only core...</div>',f.textContent="-";try{const l=await k("/api/query",{database:s,sql:n});if(r.innerHTML="",f.textContent=`Rows: ${l.row_count} | Elapsed: ${l.elapsed_ms}ms`,l.row_count===0){r.innerHTML='<div class="empty-state"><div class="desc">Query executed successfully. 0 records returned.</div></div>';return}const i=document.createElement("table");i.className="data-table";const o=document.createElement("thead"),d=document.createElement("tr");l.columns.forEach(m=>{d.innerHTML+=`<th>${v(m)}</th>`}),o.appendChild(d),i.appendChild(o);const c=document.createElement("tbody");l.rows.forEach(m=>{const y=document.createElement("tr");l.columns.forEach(p=>{const u=m[p];let g=u===null?'<span style="opacity:0.3;">NULL</span>':v(String(u));typeof u=="string"&&u.length>150&&(g=`<span title="${v(u)}">${v(u.slice(0,150))}...</span>`),y.innerHTML+=`<td>${g}</td>`}),c.appendChild(y)}),i.appendChild(c),r.appendChild(i)}catch(l){r.innerHTML=`
        <div class="empty-state" style="color: var(--break);">
          <div class="icon">✕</div>
          <div class="title" style="color: var(--break);">SQL Execution Error</div>
          <div class="desc" style="color: var(--dust-dim); margin-top: 6px;">${v(l.message)}</div>
        </div>
      `}finally{b.disabled=!1}};document.getElementById("btn-run-query").addEventListener("click",a),document.getElementById("query-sql-text").addEventListener("keydown",s=>{(s.metaKey||s.ctrlKey)&&s.key==="Enter"&&(s.preventDefault(),a())})}function j(t){if(t.innerHTML=`
    <div class="panel-header slide-in">
      <div class="panel-title">SYSTEM TELEMETRY LIVE FEED</div>
      <div class="panel-badge live" id="telemetry-connection-badge">CONNECTING...</div>
    </div>
    <div class="panel-body slide-in">
      
      <div class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">Total DB footprints</div>
          <div class="stat-value lapis" id="telemetry-db-total-size">0.00 MB</div>
          <div class="stat-sub" id="telemetry-db-count">0 database files mapped</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Active WAL files</div>
          <div class="stat-value gold" id="telemetry-wal-count">0</div>
          <div class="stat-sub">Write-Ahead Logging enabled</div>
        </div>
        <div class="stat-card">
          <div class="stat-label">Max RSS footprint</div>
          <div class="stat-value verify" id="telemetry-rss-footprint">0.00 MB</div>
          <div class="stat-sub" id="telemetry-cpu-times">CPU: u0.00s / s0.00s</div>
        </div>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px;">
        
        <!-- DB details card -->
        <div class="card" style="display:flex; flex-direction:column; min-height: 250px;">
          <div class="card-title">Database Storage Map</div>
          <div style="flex:1; overflow-y:auto;">
            <table class="data-table">
              <thead>
                <tr>
                  <th>File Name</th>
                  <th>Footprint Size</th>
                </tr>
              </thead>
              <tbody id="telemetry-db-table-body">
                <tr><td colspan="2" class="empty-state">Awaiting live feed snapshot...</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <!-- Git info card -->
        <div class="card" style="display:flex; flex-direction:column;">
          <div class="card-title">Version Control Ledger</div>
          <div style="flex: 1; display:flex; flex-direction:column; gap:16px; font-family: var(--font-mono); font-size:0.75rem; color: var(--dust-dim);">
            <div>
              <div class="stat-label">Git Sentinel Status</div>
              <div id="telemetry-git-state" style="color:var(--dust); font-weight:600; margin-top:4px;">-</div>
            </div>
            <div>
              <div class="stat-label">Current HEAD linkage</div>
              <div id="telemetry-git-head" style="color:var(--lapis-bright); margin-top:4px;">-</div>
            </div>
            <div>
              <div class="stat-label">Compressed pack footprint</div>
              <div id="telemetry-git-pack-size" style="color:var(--dust); margin-top:4px;">-</div>
            </div>
            <div style="margin-top: auto; opacity:0.3; font-size:0.6rem; border-top:1px solid var(--edge); padding-top:10px;">
              Project Root: <span id="telemetry-project-root">-</span>
            </div>
          </div>
        </div>

      </div>

    </div>
  `,x)try{x.close()}catch{}const e=document.getElementById("telemetry-connection-badge");x=O("/ws/telemetry",s=>{e.textContent="LIVE FEED",e.className="panel-badge live",document.getElementById("telemetry-db-total-size").textContent=`${s.total_db_size_mb} MB`,document.getElementById("telemetry-db-count").textContent=`${s.databases.length} database files mapped`,document.getElementById("telemetry-wal-count").textContent=s.wal_files.length,s.process&&s.process.max_rss_mb!==void 0&&(document.getElementById("telemetry-rss-footprint").textContent=`${s.process.max_rss_mb} MB`,document.getElementById("telemetry-cpu-times").textContent=`CPU: u${s.process.user_time_s}s / s${s.process.system_time_s}s`);const n=document.getElementById("telemetry-db-table-body");n.innerHTML="",s.databases.forEach(f=>{const b=document.createElement("tr");b.innerHTML=`
          <td style="color:var(--dust); font-weight:600;">${v(f.name)}</td>
          <td>${f.size_mb} MB</td>
        `,n.appendChild(b)});const r=s.git;r&&r.exists?(document.getElementById("telemetry-git-state").innerHTML='<span style="color:var(--verify);">ACTIVE & WATCHING</span>',document.getElementById("telemetry-git-head").textContent=r.head||"UNKNOWN",document.getElementById("telemetry-git-pack-size").textContent=`${r.pack_size_mb} MB`):(document.getElementById("telemetry-git-state").innerHTML='<span style="color:var(--break);">NOT INSTANTIATED</span>',document.getElementById("telemetry-git-head").textContent="None",document.getElementById("telemetry-git-pack-size").textContent="0.00 MB"),document.getElementById("telemetry-project-root").textContent=s.project_root},()=>{e.textContent="DISCONNECTED",e.className="panel-badge beta",w("error","DISCONNECTED")});const a=setInterval(()=>{if(!document.getElementById("main-content")||!document.getElementById("telemetry-connection-badge")){if(x){try{x.close()}catch{}x=null}clearInterval(a)}},1e3)}function v(t){return typeof t!="string"?"":t.replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;").replace(/'/g,"&#039;")}
