(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))n(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const l of o.addedNodes)l.tagName==="LINK"&&l.rel==="modulepreload"&&n(l)}).observe(document,{childList:!0,subtree:!0});function a(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function n(s){if(s.ep)return;s.ep=!0;const o=a(s);fetch(s.href,o)}})();const Ie="";async function $(t){const e=await fetch(`${Ie}${t}`);if(!e.ok){const a=await e.json().catch(()=>({detail:e.statusText}));throw new Error(a.detail||e.statusText)}return e.json()}async function T(t,e){const a=await fetch(`${Ie}${t}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok){const n=await a.json().catch(()=>({detail:a.statusText}));throw new Error(n.detail||a.statusText)}return a.json()}function Me(t,e,a){const n=location.protocol==="https:"?"wss:":"ws:",s={closed:!1,ws:null},o=()=>{if(s.closed)return;const l=new WebSocket(`${n}//${location.host}${t}`);s.ws=l,l.onmessage=c=>{let r;try{r=JSON.parse(c.data)}catch{return}e(r)},l.onerror=c=>a==null?void 0:a(c),l.onclose=()=>{s.closed||setTimeout(o,3e3)}};return s.close=()=>{var l;s.closed=!0;try{(l=s.ws)==null||l.close()}catch{}},o(),s}const H={};let P=null;function O(t,e){H[t]=e}function b(t){if(P===t)return;P=t,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===t)});const e=document.getElementById("main-content");H[t]&&(e.innerHTML="",H[t](e)),history.replaceState(null,"",`#${t}`)}function se(){const t=document.getElementById("main-content");P&&H[P]&&t&&(t.innerHTML="",H[P](t))}function Ce(){const t=location.hash.replace("#","");return t&&H[t]?t:"ledger"}const ae={"2e":{key:"2e",label:"2E ◐",name:"Doble Excepcionalidad (TDAH + AACC)",tachometer:!0,loopGuard:!0,restoreBanner:!0,rewards:!0,spineLabels:!1},nt:{key:"nt",label:"NT ○",name:"Neurotípico",tachometer:!1,loopGuard:!1,restoreBanner:!1,rewards:!1,spineLabels:!0}};function x(){return ae[i.cognitiveMode]||ae["2e"]}function Le(t){try{const e=JSON.parse(t||"[]");return Array.isArray(e)?e:[]}catch{return[]}}const i={cognitiveMode:localStorage.getItem("b60-cogmode")||"2e",contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:[],scratchpadOffline:Le(localStorage.getItem("b60-scratch-offline")),delegationQueue:Le(localStorage.getItem("b60-delegation")),databaseList:[],ledgerStats:null,lastVerify:null,sentinel:null,sentinelModalShown:!1,telemetrySnapshot:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasVB:{x:80,y:40,w:720,h:400},canvasAbort:null};document.addEventListener("DOMContentLoaded",async()=>{Be(i.cognitiveMode,{silent:!0}),f("indexing"),Te(),He(),Re(),Ue(),Ye(),Ke(),ze(),Oe(),Fe(),await Promise.all([Ae(),Qe(),De(),ce()]),le(),z(),f("done"),x().restoreBanner&&Ge(localStorage.getItem("b60-route")||"ledger"),b(Ce()),f("idle")});function Be(t,{silent:e=!1}={}){i.cognitiveMode=ae[t]?t:"2e",localStorage.setItem("b60-cogmode",i.cognitiveMode),document.body.classList.toggle("mode-2e",i.cognitiveMode==="2e"),document.body.classList.toggle("mode-nt",i.cognitiveMode==="nt");const a=document.getElementById("btn-cogmode");a&&(a.textContent=x().label,a.title=`Modo cognitivo: ${x().name} — click o ⌘⇧E para alternar`),e||(Te(),se(),W({icon:x().key==="2e"?"◐":"○",message:`Modo cognitivo: ${x().name}. ${x().key==="2e"?"Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos.":"Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."}`}),setTimeout(I,3e3))}function ie(){Be(i.cognitiveMode==="2e"?"nt":"2e")}function Oe(){var e;let t=document.getElementById("btn-cogmode");if(!t){const a=(e=document.getElementById("btn-bifocal"))==null?void 0:e.parentElement;if(a){const n=document.createElement("div");n.className="status-segment",n.innerHTML='<button class="status-bifocal" id="btn-cogmode"></button>',a.parentElement.insertBefore(n,a),t=n.querySelector("#btn-cogmode")}}t&&(t.textContent=x().label,t.title=`Modo cognitivo: ${x().name} — click o ⌘⇧E para alternar`,t.addEventListener("click",ie))}function f(t){i.tachometerState=t;const e=document.getElementById("tachometer");e&&(e.className=`tachometer ${t!=="idle"?t:""}`);const a=document.getElementById("status-agent-segment");if(a)if(t==="working"||t==="indexing"){a.style.display="flex";const n=document.getElementById("status-agent-text");n&&(n.textContent=t==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}const _e=[{id:"canvas",icon:"⬡",label:"Canvas",tip:"Architecture Canvas — ABSTRAER  ⌘5"},{id:"ledger",icon:"⧉",label:"Ledger",tip:"BFT Ledger — DETERMINAR  ⌘1"},{id:"databases",icon:"⛁",label:"Ontologies",tip:"Ontologies (explorador SQLite)  ⌘2"},{id:"query",icon:"❯_",label:"SQL",tip:"SQL Console (solo lectura)  ⌘3"},{id:"swarm",icon:"⚡",label:"Swarm",tip:"Agent Swarm (telemetría en vivo)  ⌘4"},{id:"analytics",icon:"∿",label:"Analytics",tip:"Ledger Analytics — DETERMINAR (agregación + BM25)  ⌘7"},{id:"sentinel",icon:"⎇",label:"Sentinel",tip:"Git Sentinel (identidad de repo + delegación real)  ⌘6"}];function Te(){const t=document.getElementById("spine");if(!t)return;t.innerHTML="";const e=document.createElement("div");e.className="spine-logo",e.title="BABYLON·60 v1.3.0",e.innerHTML='<div class="spine-logo-dot"></div>',t.appendChild(e);const a=x().spineLabels;_e.forEach((n,s)=>{if(s===1){const l=document.createElement("div");l.className="spine-separator",t.appendChild(l)}const o=document.createElement("button");o.className="spine-icon",o.dataset.route=n.id,a||(o.dataset.tooltip=n.tip),o.setAttribute("aria-label",n.tip),o.innerHTML=a?`<span class="spine-glyph">${n.icon}</span><span class="spine-label">${n.label}</span>`:n.icon,o.addEventListener("click",()=>b(n.id)),t.appendChild(o)}),ke(i.activeRoute)}function ke(t){document.querySelectorAll(".spine-icon").forEach(e=>{e.classList.toggle("active",e.dataset.route===t)})}function He(){var t;(t=document.getElementById("btn-collapse-ctx"))==null||t.addEventListener("click",oe),z()}function oe(){i.contextPaneOpen=!i.contextPaneOpen;const t=document.getElementById("context-pane"),e=document.getElementById("btn-collapse-ctx");t&&(t.classList.toggle("collapsed",!i.contextPaneOpen),e&&(e.textContent=i.contextPaneOpen?"⟨":"⟩"))}function z(){var n,s,o,l,c;const t=document.getElementById("context-pane-body");if(!t)return;const e=i.databaseList.slice(0,5).map(r=>`
    <div class="ctx-item depth-1" data-goto-db="${d(r.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${d(r.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `).join(""),a=(s=(n=i.sentinel)==null?void 0:n.warnings)!=null&&s.some(r=>r.level==="red")?'<span class="ctx-item-badge break">!</span>':(l=(o=i.sentinel)==null?void 0:o.warnings)!=null&&l.length?'<span class="ctx-item-badge gold">△</span>':'<span class="ctx-item-badge verify">ok</span>';t.innerHTML=`
    <div class="ctx-section">
      <div class="ctx-section-label">Inspector</div>
      <div class="ctx-item" data-route="canvas">
        <span class="ctx-item-icon">⬡</span>
        <span class="ctx-item-label">Architecture</span>
        <span class="ctx-item-badge verify">live</span>
      </div>
      <div class="ctx-item" data-route="ledger">
        <span class="ctx-item-icon">⧉</span>
        <span class="ctx-item-label">BFT Ledger</span>
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${((c=i.ledgerStats)==null?void 0:c.entries)??"—"}</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">${i.databaseList.length||"—"}</span>
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Analysis</div>
      <div class="ctx-item" data-route="query">
        <span class="ctx-item-icon">❯_</span>
        <span class="ctx-item-label">SQL Console</span>
      </div>
      <div class="ctx-item" data-route="swarm">
        <span class="ctx-item-icon">⚡</span>
        <span class="ctx-item-label">Agent Swarm</span>
        <span class="ctx-item-badge lapis" style="color:var(--lapis-bright)">ws</span>
      </div>
      <div class="ctx-item" data-route="sentinel">
        <span class="ctx-item-icon">⎇</span>
        <span class="ctx-item-label">Git Sentinel</span>
        ${a}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Scratchpad</div>
      <div id="ctx-scratch-preview" style="padding:4px 12px; font-size:0.65rem; color:var(--dust-faint);">
        ${i.scratchpadItems.length+i.scratchpadOffline.length===0?'<span style="color:var(--dust-ghost)">No notes yet</span>':`<span style="color:var(--dust-dim)">${i.scratchpadItems.length+i.scratchpadOffline.length} nota${i.scratchpadItems.length+i.scratchpadOffline.length!==1?"s":""} en el ledger${i.scratchpadOffline.length?` <span style="color:var(--gold)">(${i.scratchpadOffline.length} offline)</span>`:""}</span>`}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Databases</div>
      ${e||'<div style="padding:4px 12px;font-size:0.62rem;color:var(--dust-ghost)">No .db discovered</div>'}
    </div>
  `,t.querySelectorAll(".ctx-item[data-route]").forEach(r=>{r.addEventListener("click",()=>b(r.dataset.route))}),t.querySelectorAll(".ctx-item[data-goto-db]").forEach(r=>{r.addEventListener("click",()=>b("databases"))})}function K(){var a;const t=document.getElementById("ctx-db-count");t&&(t.textContent=i.databaseList.length||"—");const e=document.getElementById("ctx-ledger-count");e&&(e.textContent=((a=i.ledgerStats)==null?void 0:a.entries)??"—")}function qe(t){document.querySelectorAll(".ctx-item[data-route]").forEach(e=>{e.classList.toggle("active",e.dataset.route===t)})}function le(){var l,c,r;const t=document.getElementById("status-conn-dot"),e=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),n=document.getElementById("status-ledger-entries"),s=document.getElementById("status-lamport"),o=i.ledgerStats!==null||i.databaseList.length>0;t&&(t.className=o?"status-dot":"status-dot error"),e&&(e.textContent=o?"CONNECTED":"OFFLINE"),a&&(a.textContent=i.databaseList.length||"—"),n&&(n.textContent=((l=i.ledgerStats)==null?void 0:l.entries)??"—"),s&&(s.textContent=((r=(c=i.ledgerStats)==null?void 0:c.latest)==null?void 0:r.lamport_t)!=null?`L:${i.ledgerStats.latest.lamport_t}`:"—"),re()}function re(){var o,l;let t=document.getElementById("status-repo-segment");if(!t){const c=document.getElementById("status-bar"),r=c==null?void 0:c.querySelector(".status-segment");if(!c||!r)return;t=document.createElement("div"),t.className="status-segment",t.id="status-repo-segment",t.style.cursor="pointer",t.innerHTML='<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>',r.after(t),t.addEventListener("click",()=>b("sentinel"))}const e=document.getElementById("status-repo-text");if(!e)return;const a=i.sentinel;if(!a){e.textContent="—";return}const n=(o=a.warnings)==null?void 0:o.some(c=>c.level==="red"),s=!n&&((l=a.warnings)==null?void 0:l.length)>0;e.textContent=`${a.repo_name}${a.branch?" @"+a.branch:""}${a.head?" · "+a.head:""}${n?" ⚠":s?" △":" ✓"}`,e.style.color=n?"var(--break)":s?"var(--gold)":"var(--verify)",t.title=n?"LINAJE NO CANÓNICO — abre Git Sentinel":s?"Avisos de linaje — abre Git Sentinel":`Linaje canónico verificado (${a.commit_count??"—"} commits)`}async function De(){var t;try{i.sentinel=await $("/api/sentinel/status"),re();const e=((t=i.sentinel.warnings)==null?void 0:t.filter(a=>a.level==="red"))||[];e.length>0&&!i.sentinelModalShown&&(i.sentinelModalShown=!0,W({icon:"⚠",message:`GIT SENTINEL: ${e[0].msg}`,actions:[{label:"Abrir Sentinel",primary:!0,fn:()=>{I(),b("sentinel")}},{label:"Entendido",fn:I}]}))}catch{}}function ze(){var t;(t=document.getElementById("btn-bifocal"))==null||t.addEventListener("click",de)}function de(){i.bifocalMode=i.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",i.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",i.bifocalMode==="micro");const t=document.getElementById("btn-bifocal");t&&(t.textContent=i.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),i.bifocalMode==="macro"&&b("canvas")}const U=[{icon:"⬡",label:"Architecture Canvas",desc:"ABSTRAER: ver el sistema completo",shortcut:"⌘5",action:()=>b("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"DETERMINAR: inspector de cadena de hashes",shortcut:"⌘1",action:()=>b("ledger")},{icon:"⛁",label:"Ontologies",desc:"Explorador SQLite (solo lectura)",shortcut:"⌘2",action:()=>b("databases")},{icon:"❯_",label:"SQL Console",desc:"Consultas read-only contra cualquier .db",shortcut:"⌘3",action:()=>b("query")},{icon:"⚡",label:"Agent Swarm",desc:"Telemetría en vivo (push WS, sin polling)",shortcut:"⌘4",action:()=>b("swarm")},{icon:"∿",label:"Ledger Analytics",desc:"DETERMINAR: agregación + búsqueda BM25 del ledger",shortcut:"⌘7",action:()=>b("analytics")},{icon:"⎇",label:"Git Sentinel",desc:"Identidad de repo + delegación real (commit/push)",shortcut:"⌘6",action:()=>b("sentinel")},{icon:"⌕",label:"Search Ledger",desc:"BM25 léxico sobre payloads y taints",shortcut:"",action:()=>{b("analytics"),setTimeout(()=>{var t;return(t=document.getElementById("ledger-search-input"))==null?void 0:t.focus()},300)}},{icon:"⚿",label:"Verify Chain Integrity",desc:"Recomputar SHA3-256 de toda la cadena",shortcut:"",action:()=>{b("ledger"),setTimeout(()=>{var t;return(t=document.getElementById("btn-verify-chain"))==null?void 0:t.click()},400)}},{icon:"◐",label:"Toggle Cognitive Mode",desc:"Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",shortcut:"⌘⇧E",action:ie},{icon:"⟨",label:"Toggle Context Pane",desc:"Mostrar / ocultar mapa semántico",shortcut:"⌘B",action:oe},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Alternar vista bifocal",shortcut:"⌘M",action:de},{icon:"◎",label:"Open Scratchpad",desc:"Volcar un pensamiento sin perder foco",shortcut:"⌘⇧Space",action:()=>D(!0)}];let S=0,B=[...U];function Re(){const t=document.getElementById("palette-overlay"),e=document.getElementById("palette-input");!t||!e||(t.addEventListener("click",a=>{a.target===t&&q()}),e.addEventListener("input",()=>je(e.value)),e.addEventListener("keydown",Ve))}function Ne(){i.paletteOpen=!0;const t=document.getElementById("palette-overlay"),e=document.getElementById("palette-input");!t||!e||(t.classList.add("visible"),t.setAttribute("aria-hidden","false"),e.value="",S=0,B=[...U],F(),setTimeout(()=>e.focus(),50))}function q(){i.paletteOpen=!1;const t=document.getElementById("palette-overlay");t&&(t.classList.remove("visible"),t.setAttribute("aria-hidden","true"))}function je(t){const e=t.toLowerCase().trim();S=0,B=e?U.filter(a=>a.label.toLowerCase().includes(e)||a.desc.toLowerCase().includes(e)):[...U],F(e)}function Pe(t){return t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}function F(t=""){const e=document.getElementById("palette-results");if(e){if(B.length===0){e.innerHTML=`<div class="palette-empty">No commands match "<strong>${d(t)}</strong>"</div>`;return}e.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${B.map((a,n)=>{const s=t?a.label.replace(new RegExp(`(${Pe(t)})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${n===S?"selected":""}" data-index="${n}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${s}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,e.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const n=parseInt(a.dataset.index);B[n]&&(B[n].action(),q())}),a.addEventListener("mouseenter",()=>{S=parseInt(a.dataset.index),e.querySelectorAll(".palette-item").forEach((n,s)=>n.classList.toggle("selected",s===S))})})}}function Ve(t){var e,a;if(t.key==="Escape"){q();return}t.key==="ArrowDown"&&(t.preventDefault(),S=Math.min(S+1,B.length-1),F(((e=document.getElementById("palette-input"))==null?void 0:e.value)||"")),t.key==="ArrowUp"&&(t.preventDefault(),S=Math.max(S-1,0),F(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),t.key==="Enter"&&(t.preventDefault(),B[S]&&(B[S].action(),q()))}function Ue(){var a,n;const t=document.getElementById("scratchpad-modal"),e=document.getElementById("scratchpad-input");!t||!e||((a=document.getElementById("scratchpad-save"))==null||a.addEventListener("click",we),(n=document.getElementById("scratchpad-close"))==null||n.addEventListener("click",()=>D(!1)),e.addEventListener("keydown",s=>{s.key==="Enter"&&!s.shiftKey&&(s.preventDefault(),we()),s.key==="Escape"&&D(!1)}),Q())}function D(t){const e=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");e&&(i.scratchpadOpen=t!==void 0?t:!i.scratchpadOpen,e.classList.toggle("visible",i.scratchpadOpen),e.setAttribute("aria-hidden",String(!i.scratchpadOpen)),i.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}async function ce(){const t=[...i.scratchpadOffline];for(const e of t)try{await T("/api/cortex/notes",{text:e.text,route:e.route||""}),i.scratchpadOffline=i.scratchpadOffline.filter(a=>a.id!==e.id)}catch{break}localStorage.setItem("b60-scratch-offline",JSON.stringify(i.scratchpadOffline));try{const e=await $("/api/cortex/notes?limit=50");i.scratchpadItems=e.notes||[]}catch{}Q(),z()}async function we(){const t=document.getElementById("scratchpad-input");if(!t||!t.value.trim())return;const e=t.value.trim();t.value="";try{await T("/api/cortex/notes",{text:e,route:i.activeRoute||""}),await ce()}catch{i.scratchpadOffline.unshift({id:Date.now(),text:e,route:i.activeRoute||"",offline:!0}),i.scratchpadOffline.length>30&&i.scratchpadOffline.pop(),localStorage.setItem("b60-scratch-offline",JSON.stringify(i.scratchpadOffline)),Q(),z()}x().rewards&&(f("done"),setTimeout(()=>f("idle"),2e3))}function Q(){const t=document.getElementById("scratchpad-items");if(!t)return;const e=i.scratchpadOffline,a=i.scratchpadItems;if(e.length===0&&a.length===0){t.innerHTML="";return}const n=s=>new Date(s).toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"});t.innerHTML=[...e.map(s=>`
      <div class="scratchpad-item">
        <span class="scratchpad-item-time" style="color:var(--gold)" title="pendiente de sellar en el ledger">⚡off</span>
        <span class="scratchpad-item-text">${d(s.text)}</span>
        <span class="scratchpad-item-del" data-del-off="${s.id}" title="Descartar (aún no sellada)">✕</span>
      </div>`),...a.map(s=>`
      <div class="scratchpad-item">
        <span class="scratchpad-item-time" title="sellada en CortexLedger · ${d(s.hash||"")}${s.route?" · nació en "+d(s.route):""}">${n(s.created_at)}</span>
        <span class="scratchpad-item-text">${d(s.text)}</span>
        <span class="scratchpad-item-del" data-del-ev="${d(s.event_id)}" title="Tombstone (el ledger no olvida; la vista sí)">✕</span>
      </div>`)].join(""),t.querySelectorAll("[data-del-off]").forEach(s=>{s.addEventListener("click",o=>{o.stopPropagation();const l=parseInt(s.dataset.delOff);i.scratchpadOffline=i.scratchpadOffline.filter(c=>c.id!==l),localStorage.setItem("b60-scratch-offline",JSON.stringify(i.scratchpadOffline)),Q(),z()})}),t.querySelectorAll("[data-del-ev]").forEach(s=>{s.addEventListener("click",async o=>{o.stopPropagation();try{await T(`/api/cortex/notes/${s.dataset.delEv}/delete`,{})}catch{}await ce()})})}function W({icon:t="⬡",message:e,actions:a=[]}){const n=document.getElementById("agent-modal"),s=document.getElementById("agent-modal-icon"),o=document.getElementById("agent-modal-msg"),l=document.getElementById("agent-modal-actions");if(!n||!o||!l)return;s&&(s.textContent=t),o.textContent=e;const c=a.length>0?a:[{label:"Got it",fn:I,primary:!0}];l.innerHTML=c.map((r,u)=>`<button class="btn ${r.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${u}">${r.label}</button>`).join(""),l.querySelectorAll("button").forEach(r=>{r.addEventListener("click",()=>{var u,m;return(m=(u=c[parseInt(r.dataset.actionIdx)])==null?void 0:u.fn)==null?void 0:m.call(u)})}),n.classList.add("visible"),n.setAttribute("aria-hidden","false"),x().tachometer&&f("alert")}function I(){const t=document.getElementById("agent-modal");t&&(t.classList.remove("visible"),t.setAttribute("aria-hidden","true")),f("idle")}function Fe(){setInterval(()=>{if(!x().loopGuard||!i.loopDetector.route||i.loopDetector.interventionFired)return;if(Date.now()-i.loopDetector.routeEnteredAt>1500*1e3){i.loopDetector.interventionFired=!0;const e=i.loopDetector.route;W({icon:"⏱",message:`Llevas más de 25 minutos en ${e.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,actions:[{label:"Ver Arquitectura",primary:!0,fn:()=>{I(),b("canvas")}},{label:"Sigo aquí",fn:I},{label:"Volcar idea →",fn:()=>{I(),D(!0)}}]})}},120*1e3)}function Ge(t){var c;const e=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),n=document.getElementById("restore-points"),s=document.getElementById("restore-dismiss");if(!e||!a)return;const l=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas",sentinel:"Git Sentinel"}[t]||t}`,`${i.databaseList.length||"—"} databases available`,((c=i.ledgerStats)==null?void 0:c.entries)!=null?`${i.ledgerStats.entries} ledger entries`:"Ledger loading...",i.sentinel?`repo ${i.sentinel.repo_name}@${i.sentinel.branch??"—"}`:""].filter(Boolean);a.textContent="Session restored · ",n&&(n.innerHTML=l.map(r=>`<span class="restore-point">${d(r)}</span>`).join("")),e.style.display="flex",s==null||s.addEventListener("click",()=>{e.style.display="none"}),setTimeout(()=>{e.style.display="none"},12e3)}function Ye(){const t={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas",6:"sentinel",7:"analytics"};window.addEventListener("keydown",e=>{const a=e.metaKey||e.ctrlKey;if(a&&e.key==="k"&&!e.shiftKey){e.preventDefault(),i.paletteOpen?q():Ne();return}if(a&&e.shiftKey&&e.code==="Space"){e.preventDefault(),D();return}if(a&&e.shiftKey&&(e.key==="e"||e.key==="E")){e.preventDefault(),ie();return}if(a&&e.key==="b"&&!e.shiftKey){e.preventDefault(),oe();return}if(a&&e.key==="m"&&!e.shiftKey){e.preventDefault(),de();return}if(a&&t[e.key]){e.preventDefault(),b(t[e.key]);return}if(e.key==="Escape"){if(i.paletteOpen){q();return}if(i.scratchpadOpen){D(!1);return}Y()}})}function Ke(){O("canvas",We),O("ledger",Je),O("databases",Ze),O("query",at),O("swarm",nt),O("analytics",ut),O("sentinel",ot),window.addEventListener("hashchange",()=>{const t=window.location.hash.replace("#","");t&&b(t)})}async function Ae(){try{i.databaseList=await $("/api/databases"),K()}catch{}}async function Qe(){try{i.ledgerStats=await $("/api/ledger/stats"),K(),le()}catch{}}function k({breadcrumb:t="",actions:e=""}={}){const a=document.getElementById("focus-breadcrumb"),n=document.getElementById("focus-actions");a&&(a.innerHTML=t),n&&(n.innerHTML=e)}function A(...t){return t.map((e,a)=>a<t.length-1?`<span class="breadcrumb-item">${e}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${e}</span>`).join("")}function _(t){i.activeRoute=t,localStorage.setItem("b60-route",t),ke(t),qe(t),Y(),t!=="swarm"&&i.telemetrySocket&&(i.telemetrySocket.close(),i.telemetrySocket=null),i.loopDetector.route!==t&&(i.loopDetector.route=t,i.loopDetector.routeEnteredAt=Date.now(),i.loopDetector.interventionFired=!1)}function d(t){return String(t??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function We(t){var me,ue,pe,ve,ge,ye,fe;_("canvas"),k({breadcrumb:A("BABYLON·60","Architecture — ABSTRAER (ver el todo antes que la parte)"),actions:'<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>'});try{i.telemetrySnapshot=await $("/api/telemetry/snapshot")}catch{}const e=i.telemetrySnapshot,a=i.databaseList.length,n=((me=i.ledgerStats)==null?void 0:me.entries)??"—",s=(e==null?void 0:e.total_db_size_mb)!=null?`${e.total_db_size_mb}MB`:"—",o=i.sentinel,l=o!=null&&o.is_git?`${o.repo_name}@${o.branch??"—"} · ${o.head??"—"}`:"no git",c=(ue=o==null?void 0:o.warnings)!=null&&ue.some(g=>g.level==="red")?"err":(pe=o==null?void 0:o.warnings)!=null&&pe.length?"warn":"ok",r=[{id:"frontend",x:140,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:`Vite · modo ${x().key.toUpperCase()}`,status:"ok"},{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"14 endpoints · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger",meta:`${n} entries · SHA3-256 (huella criptográfica)`,status:(ve=i.ledgerStats)!=null&&ve.exists?"ok":"err",goto:"ledger"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Ontology DBs",meta:`${a} DBs · ${s} · RO`,status:a>0?"ok":"warn",goto:"databases"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:e?"WS push 2s (sin polling)":"offline",status:e?"ok":"warn",goto:"swarm"},{id:"git",x:140,y:240,type:"SENTINEL",name:"Git Sentinel",meta:l,status:c,goto:"sentinel"}],u=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"git",to:"fastapi"}],m={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};t.innerHTML=`
    <div class="canvas-container" id="canvas-main">
      <svg class="canvas-svg" id="canvas-svg">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="var(--edge)" />
          </marker>
        </defs>
        <g id="canvas-edges"></g>
        <g id="canvas-nodes"></g>
      </svg>
      <div class="canvas-controls">
        <button class="btn btn-icon" id="canvas-zoom-in" title="Zoom in">+</button>
        <button class="btn btn-icon" id="canvas-zoom-out" title="Zoom out">−</button>
        <button class="btn btn-icon" id="canvas-fit-btn" title="Fit all">⊞</button>
      </div>
    </div>
  `;const p=document.getElementById("canvas-svg"),E=document.getElementById("canvas-edges"),v=document.getElementById("canvas-nodes");if(!p||!E||!v)return;u.forEach(({from:g,to:y})=>{const w=r.find(Z=>Z.id===g),j=r.find(Z=>Z.id===y);if(!w||!j)return;const be=w.x+90,he=w.y+35,Ee=j.x,xe=j.y+35,C=document.createElementNS("http://www.w3.org/2000/svg","path"),$e=(be+Ee)/2;C.setAttribute("d",`M${be},${he} C${$e},${he} ${$e},${xe} ${Ee},${xe}`),C.setAttribute("stroke","var(--edge)"),C.setAttribute("stroke-width","1.5"),C.setAttribute("fill","none"),C.setAttribute("opacity","0.5"),C.setAttribute("marker-end","url(#arrow)"),E.appendChild(C)}),r.forEach(g=>{const y=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");y.setAttribute("x",g.x),y.setAttribute("y",g.y),y.setAttribute("width","195"),y.setAttribute("height","76");const w=document.createElement("div");w.className="canvas-node-card",w.style.position="relative",w.innerHTML=`
      <div class="canvas-node-type">${g.type}</div>
      <div class="canvas-node-name">${g.name}</div>
      <div class="canvas-node-meta">${d(g.meta)}</div>
      <div class="canvas-node-status" style="background:${m[g.status]||m.idle};box-shadow:0 0 5px ${m[g.status]||m.idle}"></div>
    `,g.goto&&w.addEventListener("click",()=>b(g.goto)),y.appendChild(w),v.appendChild(y)});const h=()=>p.setAttribute("viewBox",`${i.canvasVB.x} ${i.canvasVB.y} ${i.canvasVB.w} ${i.canvasVB.h}`),R=()=>{i.canvasVB={x:80,y:40,w:720,h:400},h()};R();const M=g=>{const y=i.canvasVB,w=y.x+y.w/2,j=y.y+y.h/2;y.w=Math.max(200,Math.min(2e3,y.w*g)),y.h=Math.max(110,Math.min(1100,y.h*g)),y.x=w-y.w/2,y.y=j-y.h/2,h()};(ge=document.getElementById("canvas-zoom-in"))==null||ge.addEventListener("click",()=>M(1/1.2)),(ye=document.getElementById("canvas-zoom-out"))==null||ye.addEventListener("click",()=>M(1.2)),(fe=document.getElementById("canvas-fit-btn"))==null||fe.addEventListener("click",R),p.addEventListener("wheel",g=>{g.preventDefault(),M(g.deltaY>0?1.1:1/1.1)},{passive:!1}),i.canvasAbort&&i.canvasAbort.abort(),i.canvasAbort=new AbortController;const V=i.canvasAbort.signal;let L=!1,N=0,X=0;p.addEventListener("pointerdown",g=>{L=!0,N=g.clientX,X=g.clientY}),window.addEventListener("pointermove",g=>{if(!L)return;const y=i.canvasVB.w/p.clientWidth;i.canvasVB.x-=(g.clientX-N)*y,i.canvasVB.y-=(g.clientY-X)*y,N=g.clientX,X=g.clientY,h()},{signal:V}),window.addEventListener("pointerup",()=>{L=!1},{signal:V})}let ne=1;const ee=50;async function Je(t){var e,a,n,s,o;_("ledger"),k({breadcrumb:A("BABYLON·60","BFT Ledger — DETERMINAR (verificar hasta el hash)"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),(e=document.getElementById("btn-verify-chain"))==null||e.addEventListener("click",Xe),t.innerHTML=`
    <div class="stats-grid slide-in" id="ledger-stats-grid">
      <div class="stat-card">
        <div class="stat-label">Ledger File</div>
        <div class="stat-value lapis" id="stat-db-name" style="font-size:0.85rem">—</div>
        <div class="stat-sub">SQLite WAL (diario de escritura: nunca corrompe) · RO</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Entries</div>
        <div class="stat-value gold" id="stat-total-entries">0</div>
        <div class="stat-sub" id="stat-latest-time">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label" title="Cada hash sella al anterior: manipular una entrada rompe la cadena entera">Consensus</div>
        <div class="stat-value verify" id="stat-integrity">UNKNOWN</div>
        <div class="stat-sub" id="stat-latest-lamport">Lamport (reloj lógico causal): —</div>
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title">Hash Chain Verification</div>
        <span id="verify-summary" style="font-size:0.62rem;color:var(--dust-faint)"></span>
      </div>
      <div class="verify-progress" id="verify-progress-wrap" style="display:none">
        <div class="verify-progress-bar" id="verify-progress-bar"></div>
      </div>
      <div id="chain-visual-grid" class="chain-container">
        <div class="empty-state" style="padding:20px 0">
          <div class="icon">⚿</div>
          <div class="desc">Click "Verify Chain" para recomputar SHA3-256 (huella digital de cada evento) y asertar integridad.</div>
        </div>
      </div>
    </div>

    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ledger Sequence</div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Seq</th>
              <th>Stream</th>
              <th>Entity</th>
              <th>Event Type</th>
              <th title="Reloj lógico: orden causal sin depender del reloj de pared">Lamport</th>
              <th title="Huella causal: quién escribió, con qué motor y por qué">Taint</th>
              <th>Timestamp</th>
              <th title="SHA3-256: huella digital criptográfica del evento">Hash</th>
            </tr>
          </thead>
          <tbody id="ledger-table-body">
            <tr><td colspan="8" style="text-align:center;padding:16px;color:var(--dust-ghost)">Loading...</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button class="btn" id="btn-ledger-prev" disabled>◀ Prev</button>
        <span style="font-family:var(--font-mono);font-size:0.72rem" id="ledger-page-info">Page 1</span>
        <button class="btn" id="btn-ledger-next" disabled>Next ▶</button>
      </div>
    </div>

    <div id="entry-detail-panel" class="detail-panel" aria-hidden="true"></div>
  `;try{const l=await $("/api/ledger/stats");i.ledgerStats=l;const c=document.getElementById("stat-db-name");c&&(c.textContent=l.db_path||"—");const r=document.getElementById("stat-total-entries");r&&(r.textContent=l.entries??0);const u=document.getElementById("stat-latest-lamport");u&&(u.textContent=`Lamport (reloj lógico causal): ${((a=l.latest)==null?void 0:a.lamport_t)??"—"}`);const m=document.getElementById("stat-latest-time");m&&((n=l.latest)!=null&&n.created_at)&&(m.textContent=String(l.latest.created_at).slice(0,19)),le(),K()}catch{}await te(1),(s=document.getElementById("btn-ledger-prev"))==null||s.addEventListener("click",()=>te(ne-1)),(o=document.getElementById("btn-ledger-next"))==null||o.addEventListener("click",()=>te(ne+1))}async function te(t){t<1&&(t=1),ne=t;const e=document.getElementById("ledger-table-body");if(e)try{const a=(t-1)*ee,n=await $(`/api/ledger/entries?limit=${ee}&offset=${a}`),s=n.entries||[],o=n.total??s.length;s.length===0?e.innerHTML='<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>':(e.innerHTML=s.map(m=>`
        <tr data-seq="${m.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${m.seq}</td>
          <td class="stream-cell">${d(m.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${d(m.entity_id)}</td>
          <td>${d(m.event_type)}</td>
          <td style="color:var(--dust-dim)">${m.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${d(m.cortex_taint)}">${d((m.cortex_taint||"—").slice(0,26))}${(m.cortex_taint||"").length>26?"…":""}</td>
          <td class="time-cell">${String(m.created_at||"").slice(0,19)}</td>
          <td class="hash-cell" title="${d(m.entry_hash)}">${(m.entry_hash||"—").slice(0,12)}…</td>
        </tr>
      `).join(""),e.querySelectorAll("tr[data-seq]").forEach(m=>{m.addEventListener("click",()=>G(parseInt(m.dataset.seq)))}));const l=Math.max(1,Math.ceil(o/ee)),c=document.getElementById("ledger-page-info");c&&(c.textContent=`Page ${t} / ${l} · ${o} entries`);const r=document.getElementById("btn-ledger-prev"),u=document.getElementById("btn-ledger-next");r&&(r.disabled=t<=1),u&&(u.disabled=t>=l)}catch(a){e.innerHTML=`<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${d(a.message)}</td></tr>`}}async function G(t){var a,n;const e=document.getElementById("entry-detail-panel");if(e){e.classList.add("open"),e.setAttribute("aria-hidden","false"),e.innerHTML=`<div class="detail-header"><span class="detail-title">⧉ Entry #${t}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`,(a=e.querySelector("#detail-close"))==null||a.addEventListener("click",Y);try{const s=await $(`/api/ledger/entry/${t}`);let o=s.payload_json||"";try{o=JSON.stringify(JSON.parse(s.payload_json),null,2)}catch{}const l=(c,r,u="")=>`
      <div class="detail-field">
        <div class="detail-field-label">${c}</div>
        <div class="detail-field-value ${u}">${d(r??"—")}</div>
      </div>`;e.innerHTML=`
      <div class="detail-header">
        <span class="detail-title">⧉ Entry #${s.seq} · ${d(s.event_type)}</span>
        <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button>
      </div>
      <div class="detail-body">
        ${l("Event ID (UUID v5: determinista, mismo input → mismo id)",s.event_id,"mono")}
        ${l("Stream · Entity",`${s.stream} · ${s.entity_id}`)}
        ${l("Lamport T (reloj lógico: orden causal)",s.lamport_t)}
        ${l("Causal Taint (quién/por qué escribió)",s.cortex_taint,"mono")}
        ${l("Source (origen del dato)",`${s.source_db??"—"} › ${s.source_table??"—"} › ${s.source_pk??"—"}`,"mono")}
        ${l("Created At",s.created_at,"mono")}
        ${l("Prev Hash (sello del evento anterior)",s.prev_hash,"mono hash")}
        ${l("Entry Hash (SHA3-256 de todo el sobre)",s.entry_hash,"mono hash")}
        <div class="detail-field">
          <div class="detail-field-label">Payload (contenido del evento)</div>
          <pre class="detail-payload">${d(o)}</pre>
        </div>
      </div>
    `,(n=e.querySelector("#detail-close"))==null||n.addEventListener("click",Y)}catch(s){const o=e.querySelector(".detail-body");o&&(o.innerHTML=`<span style="color:var(--break)">${d(s.message)}</span>`)}}}function Y(){const t=document.getElementById("entry-detail-panel");t&&(t.classList.remove("open"),t.setAttribute("aria-hidden","true"))}async function Xe(){const t=document.getElementById("btn-verify-chain"),e=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),n=document.getElementById("verify-progress-bar"),s=document.getElementById("stat-integrity"),o=document.getElementById("verify-summary");if(!e)return;t&&(t.disabled=!0,t.textContent="⚙ Verifying..."),a&&(a.style.display="block"),f("working");let l=0;const c=setInterval(()=>{l=Math.min(l+8,90),n&&(n.style.width=`${l}%`)},120);try{const r=await T("/api/ledger/verify",{});i.lastVerify=r,clearInterval(c),n&&(n.style.width="100%");const u=r.total_entries??0,m=r.verified_entries??0,p=u-m;e.innerHTML="",(r.entries||[]).slice(0,400).forEach(v=>{const h=document.createElement("div");h.className=`chain-block ${v.valid?"":"invalid"}`,h.title=`Seq ${v.seq} · L:${v.lamport_t} · ${v.valid?"VALID":v.errors.join(" · ")}`,h.addEventListener("click",()=>G(v.seq)),e.appendChild(h)}),u===0&&(e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>');const E=r.broken_at!=null;if(s&&(s.textContent=r.valid?"VERIFIED":E?`BROKEN (${p})`:"ERROR",s.className=`stat-value ${r.valid?"verify":"break"}`),o&&(o.textContent=r.valid?`${m}/${u} entries · cadena SHA3-256 intacta`:E?`rota en seq ${r.broken_at} · ${m}/${u} válidas`:r.error||"verificación fallida"),!r.valid&&r.error&&u===0&&(e.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(r.error)}</div>`),r.valid){if(f("done"),x().rewards){const v=document.getElementById("main-content");v==null||v.classList.add("reward-active"),setTimeout(()=>v==null?void 0:v.classList.remove("reward-active"),1400)}}else f("alert"),W({icon:"⚠",message:E?`Violación de integridad en seq ${r.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`:`Verificación fallida: ${r.error||"error desconocido"}.`,actions:E?[{label:"Inspeccionar entrada",primary:!0,fn:()=>{I(),G(r.broken_at)}},{label:"Cerrar",fn:I}]:[{label:"Cerrar",primary:!0,fn:I}]});setTimeout(()=>f("idle"),3e3)}catch(r){clearInterval(c),e.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${d(r.message)}</div>`,f("idle")}t&&(t.disabled=!1,t.textContent="⚿ Verify Chain"),a&&setTimeout(()=>{a.style.display="none"},1500)}async function Ze(t){_("databases"),k({breadcrumb:A("BABYLON·60","Ontologies")}),t.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card">
        <div class="stat-label">SQLite Files</div>
        <div class="stat-value gold" id="db-total-count">—</div>
        <div class="stat-sub">Descubiertos en la raíz del proyecto</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Size</div>
        <div class="stat-value lapis" id="db-total-size" style="font-size:1.1rem">—</div>
        <div class="stat-sub">Huella en disco</div>
      </div>
    </div>
    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ontology Databases <span style="color:var(--dust-ghost);font-weight:400;font-size:0.62rem">(click = ver tablas)</span></div>
      <table class="data-table">
        <thead><tr><th>Database</th><th>Size</th><th>Type</th></tr></thead>
        <tbody id="db-table-body"><tr><td colspan="3" style="text-align:center;padding:14px;color:var(--dust-ghost)">Loading...</td></tr></tbody>
      </table>
    </div>
    <div class="card fade-in" style="margin-top:14px;display:none" id="db-tables-panel">
      <div class="card-title" id="db-tables-title">Tables</div>
      <div id="db-tables-body" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px"></div>
    </div>
    <div class="card fade-in" style="margin-top:14px;display:none" id="db-browse-panel">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div class="card-title" id="db-browse-title">Table</div>
        <span id="db-browse-meta" style="font-size:0.6rem;color:var(--dust-ghost)"></span>
      </div>
      <div id="db-schema-body" style="font-family:var(--font-mono);font-size:0.68rem;color:var(--dust-dim);margin-bottom:10px"></div>
      <div id="db-rows-body" style="overflow-x:auto"></div>
    </div>
  `;try{const e=await $("/api/databases");i.databaseList=e,K();const a=document.getElementById("db-table-body"),n=document.getElementById("db-total-count"),s=document.getElementById("db-total-size");if(n&&(n.textContent=e.length),s){const l=e.reduce((c,r)=>c+(r.size_bytes||0),0);s.textContent=l>1e6?`${(l/1e6).toFixed(1)} MB`:`${(l/1024).toFixed(0)} KB`}const o=l=>l.includes("ledger")?"LEDGER":l.includes("ontology")?"ONTOLOGY":l.includes("memory")||l.includes("cortex")?"CORTEX":l.includes("telemetry")?"TELEMETRY":l.includes("nexus")?"NEXUS":"GENERAL";a&&(a.innerHTML=e.map(l=>`
      <tr style="cursor:pointer" data-db="${d(l.name)}" title="Browse tables">
        <td class="stream-cell">${d(l.name)}</td>
        <td class="time-cell">${d(l.size_human||"—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${o(l.name)}</span></td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-db]").forEach(l=>{l.addEventListener("click",()=>et(l.dataset.db))})}catch(e){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${d(e.message)}</td></tr>`)}}async function et(t){const e=document.getElementById("db-tables-panel"),a=document.getElementById("db-tables-title"),n=document.getElementById("db-tables-body"),s=document.getElementById("db-browse-panel");if(!(!e||!n)){e.style.display="block",s&&(s.style.display="none"),a&&(a.textContent=`Tables — ${t}`),n.innerHTML='<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>',k({breadcrumb:A("BABYLON·60","Ontologies",t)});try{const o=await $(`/api/databases/${encodeURIComponent(t)}/tables`);if(o.length===0){n.innerHTML='<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>';return}n.innerHTML=o.map(l=>`
      <button class="btn" data-table="${d(l.name)}" style="font-size:0.62rem">
        ${d(l.name)} <span style="color:var(--gold);margin-left:4px">${l.row_count}</span>
      </button>
    `).join(""),n.querySelectorAll("[data-table]").forEach(l=>{l.addEventListener("click",()=>tt(t,l.dataset.table))})}catch(o){n.innerHTML=`<span style="color:var(--break);font-size:0.68rem">${d(o.message)}</span>`}}}async function tt(t,e){const a=document.getElementById("db-browse-panel"),n=document.getElementById("db-browse-title"),s=document.getElementById("db-browse-meta"),o=document.getElementById("db-schema-body"),l=document.getElementById("db-rows-body");if(!(!a||!l)){a.style.display="block",n&&(n.textContent=`${t} › ${e}`),o&&(o.textContent="Loading schema..."),l.innerHTML="",k({breadcrumb:A("BABYLON·60","Ontologies",t,e)});try{const[c,r]=await Promise.all([$(`/api/databases/${encodeURIComponent(t)}/schema/${encodeURIComponent(e)}`),$(`/api/databases/${encodeURIComponent(t)}/tables/${encodeURIComponent(e)}?limit=25`)]);o&&(o.innerHTML=c.map(u=>`<span style="margin-right:12px;white-space:nowrap">${u.pk?"⚿":"·"} ${d(u.name)} <span style="color:var(--dust-ghost)">${d(u.type||"")}</span></span>`).join("")),s&&(s.textContent=`${r.total} rows total · showing ${r.rows.length}`),r.rows.length===0?l.innerHTML='<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>':l.innerHTML=`
        <table class="data-table">
          <thead><tr>${r.columns.map(u=>`<th>${d(u)}</th>`).join("")}</tr></thead>
          <tbody>${r.rows.map(u=>`
            <tr>${r.columns.map(m=>{let p=u[m];p==null&&(p="—"),p=String(p);const E=p.length>90?p.slice(0,90)+"…":p;return`<td title="${d(p.slice(0,400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(E)}</td>`}).join("")}</tr>
          `).join("")}</tbody>
        </table>
      `}catch(c){l.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(c.message)}</div>`}}}async function at(t){var a,n,s;_("query"),k({breadcrumb:A("BABYLON·60","SQL Console")}),i.databaseList.length===0&&await Ae(),t.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${i.databaseList.map(o=>`<option value="${d(o.name)}">${d(o.name)}</option>`).join("")}
        </select>
        <button class="btn btn-primary" id="btn-run-query">▶ Run</button>
        <button class="btn" id="btn-clear-query">Clear</button>
      </div>
      <div class="code-editor">
        <textarea id="query-input" placeholder="SELECT * FROM ledger_entries LIMIT 20;" spellcheck="false"></textarea>
        <div class="code-editor-toolbar">
          <span style="font-size:0.58rem;color:var(--dust-ghost)">query_only=ON (candado a nivel de motor: imposible mutar) · INSERT/UPDATE/DDL bloqueados</span>
          <span style="font-size:0.58rem;color:var(--dust-ghost)">Shift+Enter to run</span>
        </div>
      </div>
    </div>
    <div id="query-result-card" class="card fade-in" style="display:none">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title" id="query-result-title">Results</div>
        <span id="query-result-meta" style="font-size:0.6rem;color:var(--dust-ghost)"></span>
      </div>
      <div id="query-result-body" style="overflow-x:auto"></div>
    </div>
  `;const e=async()=>{var m,p,E;const o=(p=(m=document.getElementById("query-input"))==null?void 0:m.value)==null?void 0:p.trim(),l=(E=document.getElementById("query-db-select"))==null?void 0:E.value;if(!o||!l)return;f("working");const c=document.getElementById("query-result-card"),r=document.getElementById("query-result-body"),u=document.getElementById("query-result-meta");c&&(c.style.display="block"),r&&(r.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const v=await T("/api/query",{database:l,sql:o}),h=v.rows||[],R=v.columns||[];u&&(u.textContent=`${v.row_count??h.length} rows${v.truncated?" (truncado a 1000 — afina la consulta)":""} · ${v.elapsed_ms??"—"}ms · ${v.database}`),r&&(h.length===0?r.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':r.innerHTML=`
            <table class="data-table">
              <thead><tr>${R.map(M=>`<th>${d(M)}</th>`).join("")}</tr></thead>
              <tbody>${h.map(M=>`<tr>${R.map(V=>{let L=M[V];L==null&&(L=""),L=String(L);const N=L.length>120?L.slice(0,120)+"…":L;return`<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d(L.slice(0,400))}">${d(N)}</td>`}).join("")}</tr>`).join("")}</tbody>
            </table>
          `),f("done"),setTimeout(()=>f("idle"),2e3)}catch(v){r&&(r.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${d(v.message)}</div>`),f("idle")}};(a=document.getElementById("btn-run-query"))==null||a.addEventListener("click",e),(n=document.getElementById("btn-clear-query"))==null||n.addEventListener("click",()=>{const o=document.getElementById("query-input");o&&(o.value="");const l=document.getElementById("query-result-card");l&&(l.style.display="none")}),(s=document.getElementById("query-input"))==null||s.addEventListener("keydown",o=>{o.shiftKey&&o.key==="Enter"&&(o.preventDefault(),e())})}async function nt(t){if(_("swarm"),k({breadcrumb:A("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'}),t.innerHTML=`
    <div class="swarm-layout">
      <div class="swarm-terminal">
        <div class="swarm-terminal-header">
          <div class="status-dot" style="width:5px;height:5px;border-radius:50%;background:var(--verify)"></div>
          Telemetry Stream · push cada 2s (el servidor empuja: la UI nunca pregunta)
        </div>
        <div class="swarm-terminal-body" id="swarm-log-body">
          <div class="swarm-log-line"><span class="swarm-log-time">—:—</span><span class="swarm-log-agent">SYSTEM</span><span class="swarm-log-msg">Connecting to /ws/telemetry...</span></div>
        </div>
      </div>
      <div class="swarm-inspector">
        <div class="swarm-inspector-header">Agent State</div>
        <div class="swarm-inspector-body" id="swarm-agents"></div>
      </div>
    </div>
  `,st(),i.telemetrySocket)try{i.telemetrySocket.close()}catch{}f("indexing"),i.telemetrySocket=Me("/ws/telemetry",e=>{i.telemetrySnapshot=e,it(e),i.tachometerState==="indexing"&&f("idle")},()=>{i.tachometerState==="indexing"&&f("idle")})}function st(){var s;const t=document.getElementById("swarm-agents");if(!t)return;const e=i.lastVerify,a=i.sentinel,n=[{name:"MOSKV-1 APEX",status:"idle",task:"Meta-orquestador · esperando directiva",progress:0},{name:"BFT Verifier",status:e?e.valid?"done":"error":"idle",task:e?e.valid?`Cadena verificada: ${e.verified_entries}/${e.total_entries}`:`ROTA en seq ${e.broken_at}`:"Sin verificación en esta sesión",progress:e?100:0},{name:"Git Sentinel",status:a?(s=a.warnings)!=null&&s.some(o=>o.level==="red")?"error":"done":"idle",task:a?`${a.repo_name}@${a.branch??"—"} · ${a.dirty_files} dirty · delegación 100% al agente`:"Sin datos de repo",progress:a?100:0},{name:"Telemetry Stream",status:"running",task:"Empujando snapshots del sistema vía WS",progress:100}];t.innerHTML=n.map(o=>`
    <div class="agent-card">
      <div class="agent-card-header">
        <span class="agent-name">${o.name}</span>
        <span class="agent-status-pill ${o.status}">${o.status.toUpperCase()}</span>
      </div>
      <div class="agent-task">${d(o.task)}</div>
      <div class="agent-progress">
        <div class="agent-progress-fill ${o.status==="done"?"done":""}" style="width:${o.progress}%"></div>
      </div>
    </div>
  `).join("")}function it(t){var u,m,p,E;const e=document.getElementById("swarm-log-body");if(!e)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),n=((u=t.databases)==null?void 0:u.length)??0,s=t.total_db_size_mb!=null?`${t.total_db_size_mb}MB`:"—",o=((m=t.wal_files)==null?void 0:m.length)??0,l=((p=t.process)==null?void 0:p.max_rss_mb)!=null?`${t.process.max_rss_mb}MB`:"—",c=(E=t.git)!=null&&E.head?t.git.head.replace("ref: refs/heads/","@"):"",r=document.createElement("div");for(r.className="swarm-log-line",r.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${n} DBs · ${s} · WAL×${o} · RSS ${l} ${c?"· "+d(c):""}</span>
  `,e.appendChild(r);e.children.length>200;)e.removeChild(e.firstChild);e.scrollTop=e.scrollHeight,i.swarmLog.push({time:a,snap:t}),i.swarmLog.length>200&&i.swarmLog.shift()}async function ot(t){var l,c,r,u;_("sentinel"),k({breadcrumb:A("BABYLON·60","Git Sentinel"),actions:'<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>'}),t.innerHTML='<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>';try{i.sentinel=await $("/api/sentinel/status")}catch(m){t.innerHTML=`<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${d(m.message)}</div></div>`;return}re(),z();const e=i.sentinel,a=e.warnings.filter(m=>m.level==="red");e.warnings.filter(m=>m.level==="amber");const n=a.length===0,s=e.warnings.length===0?'<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>':e.warnings.map(m=>`
        <div class="sentinel-warning ${m.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${d(m.msg)}</span>
        </div>
      `).join(""),o=e.remotes.length===0?'<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>':e.remotes.map(m=>`<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${d(m.name)} → ${d(m.url)}</div>`).join("");t.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card" style="border-left:2px solid ${n?"var(--verify)":"var(--break)"}">
        <div class="stat-label">Repo Actual (recalcado siempre — abajo en la barra de estado también)</div>
        <div class="stat-value ${n?"verify":"break"}" style="font-size:1rem">${d(e.repo_name)}</div>
        <div class="stat-sub">@${d(e.branch??"—")} · HEAD ${d(e.head??"—")} · ${e.commit_count??"—"} commits</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Working Tree (árbol de trabajo: cambios sin commitear)</div>
        <div class="stat-value gold">${e.dirty_files}</div>
        <div class="stat-sub">${e.dirty_files===0?"Limpio — todo sellado en git":"ficheros sucios pendientes de commit"}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Último Commit</div>
        <div class="stat-value lapis" style="font-size:0.78rem">${d((e.head_subject||"—").slice(0,44))}</div>
        <div class="stat-sub">${d(String(e.head_time||"—").slice(0,19))}</div>
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Lineage Guard (intuición de repo incorrecto)</div>
      ${s}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--edge-soft)">
        <div style="font-size:0.6rem;color:var(--dust-ghost);margin-bottom:4px">CANON: ${d(e.canonical.repo_name)} @ ${d(e.canonical.branch)} · remotos: ${d(e.canonical.remote_policy)}</div>
        ${o}
      </div>
    </div>

    <div class="card fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <div class="card-title">Delegación 100% al Agente <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(sellada en CortexLedger real)</span></div>
        <button class="btn" id="btn-verify-ide-ledger" style="font-size:0.6rem">⚿ Verify IDE Ledger</button>
      </div>
      <div style="font-size:0.66rem;color:var(--dust-dim);margin-bottom:10px">
        Declaras la intención; MOSKV-1 ejecuta con Git Sentinel y la sella en el ledger propio del IDE (append-only, hash-chain SHA-256).
        <code style="color:var(--verify)">commit</code> se ejecuta de verdad (git local); <code style="color:var(--gold)">push/merge/ship/deploy</code> hacen <b>crash causal</b> mientras P0 esté abierto (claves expuestas en el fork remoto).
      </div>
      <div style="display:flex;gap:6px;margin-bottom:10px">
        <select class="select" id="delegation-kind" style="width:120px">
          <option value="commit">commit</option>
          <option value="precommit">precommit</option>
          <option value="status">status</option>
          <option value="push">push ⛔</option>
          <option value="merge">merge ⛔</option>
          <option value="ship">ship ⛔</option>
          <option value="deploy">deploy ⛔</option>
          <option value="custom">custom</option>
        </select>
        <input class="input" id="delegation-input" placeholder="Directiva… ej: 'feat(ide): analytics + delegación real'" style="flex:1">
        <button class="btn btn-primary" id="delegation-add">⚡ Delegar</button>
      </div>
      <div id="delegation-status" style="font-size:0.62rem;margin-bottom:8px;min-height:14px"></div>
      <div id="delegation-list"><div style="color:var(--dust-ghost);font-size:0.64rem">Cargando cola…</div></div>
    </div>
  `,(l=document.getElementById("btn-sentinel-refresh"))==null||l.addEventListener("click",()=>se()),(c=document.getElementById("delegation-add"))==null||c.addEventListener("click",Se),(r=document.getElementById("delegation-input"))==null||r.addEventListener("keydown",m=>{m.key==="Enter"&&Se()}),(u=document.getElementById("btn-verify-ide-ledger"))==null||u.addEventListener("click",dt),await J()}async function J(){const t=document.getElementById("delegation-list");if(t)try{const e=await $("/api/delegation");mt(e.delegations||[])}catch(e){t.innerHTML=`<div style="color:var(--break);font-size:0.64rem">${d(e.message)}</div>`}}async function Se(){const t=document.getElementById("delegation-input"),e=document.getElementById("delegation-kind"),a=document.getElementById("delegation-status");if(!t||!t.value.trim())return;const n=t.value.trim(),s=(e==null?void 0:e.value)||"custom";try{const o=await T("/api/delegation",{directive:n,kind:s});t.value="",a&&(a.innerHTML=o.cloud_blocked?`<span style="color:var(--gold)">⛔ '${s}' encolado pero bloqueado por P0 — ejecútalo para ver el crash causal.</span>`:`<span style="color:var(--verify)">✓ '${s}' encolado (${o.delegation_id}).</span>`),x().rewards&&(f("done"),setTimeout(()=>f("idle"),1500)),await J()}catch(o){a&&(a.innerHTML=`<span style="color:var(--break)">${d(o.message)}</span>`)}}async function lt(t){const e=document.getElementById("delegation-status");e&&(e.innerHTML=`<span style="color:var(--dust-faint)">Ejecutando ${t}…</span>`);try{const a=await T(`/api/delegation/${t}/execute`,{});if(e&&(e.innerHTML=`<span style="color:var(--verify)">✓ EXECUTED: ${d(a.result||"")}</span>`),x().rewards){const n=document.getElementById("main-content");n==null||n.classList.add("reward-active"),setTimeout(()=>n==null?void 0:n.classList.remove("reward-active"),1400)}}catch(a){e&&(e.innerHTML=`<span style="color:var(--break)">⛔ ${d(a.message)}</span>`),f("alert"),setTimeout(()=>f("idle"),2500)}await J()}async function rt(t){try{await T(`/api/delegation/${t}/cancel`,{})}catch{}await J()}async function dt(){const t=document.getElementById("delegation-status");try{const e=await T("/api/delegation/verify",{});t&&(t.innerHTML=e.valid?`<span style="color:var(--verify)">⚿ IDE CortexLedger íntegro: ${e.verified_entries}/${e.total_entries} eventos, cadena SHA-256 intacta.</span>`:`<span style="color:var(--break)">⚿ Cadena rota en seq ${e.broken_at} (${e.verified_entries}/${e.total_entries}).</span>`)}catch(e){t&&(t.innerHTML=`<span style="color:var(--break)">${d(e.message)}</span>`)}}const ct={QUEUED:"var(--gold)",EXECUTED:"var(--verify)",BLOCKED:"var(--break)",FAILED:"var(--break)",CANCELLED:"var(--dust-ghost)"};function mt(t){const e=document.getElementById("delegation-list");if(!e)return;if(!t||t.length===0){e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>';return}const a=new Set(["push","merge","ship","deploy"]);e.innerHTML=t.map(n=>{const s=n.state==="QUEUED",o=a.has(n.kind);return`
    <div class="delegation-item">
      <span class="delegation-state" style="color:${ct[n.state]||"var(--dust-dim)"};background:transparent;border:1px solid currentColor">${n.state}</span>
      <span class="delegation-kind-tag" title="${o?"op de nube — bloqueada por P0":"op local"}">${d(n.kind)}${o?" ⛔":""}</span>
      <span class="delegation-text">${d(n.directive)}${n.result?` <span style="color:var(--dust-faint)">— ${d(String(n.result).slice(0,80))}</span>`:""}</span>
      ${s?`<button class="btn delegation-exec" data-exec="${n.delegation_id}" style="font-size:0.56rem;padding:2px 7px">▶ EJECUTAR</button>`:""}
      ${s?`<span class="delegation-del" data-del="${n.delegation_id}" title="Cancelar">✕</span>`:""}
    </div>`}).join(""),e.querySelectorAll("[data-exec]").forEach(n=>n.addEventListener("click",()=>lt(n.dataset.exec))),e.querySelectorAll("[data-del]").forEach(n=>n.addEventListener("click",()=>rt(n.dataset.del)))}async function ut(t){var n,s,o;_("analytics"),k({breadcrumb:A("BABYLON·60","Ledger Analytics — DETERMINAR"),actions:'<button class="btn" id="btn-analytics-refresh" style="font-size:0.62rem">↺ Refresh</button>'}),t.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Búsqueda semántico-léxica <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(Okapi BM25 sobre payload+taint — el "por qué macro")</span></div>
      <div style="display:flex;gap:8px">
        <input class="input" id="ledger-search-input" placeholder="Buscar en el ledger… ej: 'amendment risk', 'autopoietic', 'enrollment'" style="flex:1">
        <button class="btn btn-primary" id="ledger-search-btn">⌕ Buscar</button>
      </div>
      <div id="ledger-search-results" style="margin-top:10px"></div>
    </div>
    <div id="analytics-body">
      <div class="empty-state" style="padding:20px 0"><div class="icon">∿</div><div class="desc">Cargando agregación del ledger…</div></div>
    </div>
    <div id="entry-detail-panel" class="detail-panel" aria-hidden="true"></div>
  `,(n=document.getElementById("btn-analytics-refresh"))==null||n.addEventListener("click",()=>se());const e=()=>{var l;return pt(((l=document.getElementById("ledger-search-input"))==null?void 0:l.value)||"")};(s=document.getElementById("ledger-search-btn"))==null||s.addEventListener("click",e),(o=document.getElementById("ledger-search-input"))==null||o.addEventListener("keydown",l=>{l.key==="Enter"&&e()});const a=document.getElementById("analytics-body");try{const l=await $("/api/ledger/analytics"),c=(u,m,p,E)=>{const v=Math.max(...u.map(h=>h[p]),1);return u.map(h=>`
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span style="width:150px;font-size:0.64rem;color:var(--dust-dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d(String(h[m]))}">${d(String(h[m]))}</span>
          <div style="flex:1;background:var(--tablet);border-radius:2px;height:14px;position:relative">
            <div style="width:${(h[p]/v*100).toFixed(1)}%;background:${E};height:100%;border-radius:2px;opacity:0.75"></div>
          </div>
          <span style="width:40px;text-align:right;font-size:0.62rem;color:var(--gold)">${h[p]}</span>
        </div>`).join("")},r=l.lamport;a.innerHTML=`
      <div class="stats-grid" style="margin-bottom:14px">
        <div class="stat-card"><div class="stat-label">Total Eventos</div><div class="stat-value gold">${l.total_entries}</div><div class="stat-sub">${d(l.db_path)}</div></div>
        <div class="stat-card"><div class="stat-label" title="Reloj lógico: sin huecos = orden causal total reconstruible">Continuidad Lamport</div><div class="stat-value ${r.contiguous?"verify":"break"}">${r.contiguous?"CONTIGUA":`${r.gaps} HUECOS`}</div><div class="stat-sub">L:${r.min}–${r.max} · ${r.distinct} distintos</div></div>
        <div class="stat-card"><div class="stat-label">Span Temporal</div><div class="stat-value lapis" style="font-size:0.8rem">${String(l.time_span.first||"—").slice(0,10)}</div><div class="stat-sub">→ ${String(l.time_span.last||"—").slice(0,10)}</div></div>
      </div>
      <div class="card" style="margin-bottom:12px"><div class="card-title" style="margin-bottom:8px">Streams</div>${c(l.streams,"stream","count","var(--lapis-bright)")}</div>
      <div class="card" style="margin-bottom:12px"><div class="card-title" style="margin-bottom:8px">Event Types</div>${c(l.event_types,"event_type","count","var(--verify)")}</div>
      <div class="card"><div class="card-title" style="margin-bottom:8px">Agentes <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(prefijo del causal_taint — quién escribió)</span></div>${c(l.agents,"agent","count","var(--gold)")}</div>
    `}catch(l){a.innerHTML=`<div class="empty-state" style="padding:24px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${d(l.message)}</div></div>`}}async function pt(t){const e=document.getElementById("ledger-search-results");if(e){if(!t.trim()){e.innerHTML="";return}e.innerHTML='<div style="color:var(--dust-faint);font-size:0.64rem">Rankeando…</div>';try{const a=await $(`/api/ledger/search?q=${encodeURIComponent(t)}&limit=15`);if(!a.results.length){e.innerHTML=`<div style="color:var(--dust-ghost);font-size:0.64rem">Sin coincidencias léxicas para «${d(t)}» en ${a.corpus_size} eventos.</div>`;return}e.innerHTML=`
      <div style="font-size:0.58rem;color:var(--dust-ghost);margin-bottom:6px">${a.results.length} resultados · ${d(a.method)} · corpus ${a.corpus_size}${a.truncated?` · escaneados ${a.scanned}/${a.total} (truncado)`:""}</div>
      ${a.results.map(n=>`
        <div class="search-hit" data-seq="${n.seq}" title="Abrir entrada #${n.seq}">
          <span class="search-score">${n.score.toFixed(2)}</span>
          <div style="flex:1;min-width:0">
            <div style="font-size:0.64rem;color:var(--dust-dim)"><b>#${n.seq}</b> · ${d(n.event_type)} · ${d(n.stream)}</div>
            <div style="font-size:0.58rem;color:var(--dust-faint);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(n.snippet)}</div>
          </div>
        </div>`).join("")}
    `,e.querySelectorAll("[data-seq]").forEach(n=>n.addEventListener("click",()=>G(parseInt(n.dataset.seq))))}catch(a){e.innerHTML=`<div style="color:var(--break);font-size:0.64rem">${d(a.message)}</div>`}}}
