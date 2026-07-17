(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))s(n);new MutationObserver(n=>{for(const c of n)if(c.type==="childList")for(const o of c.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&s(o)}).observe(document,{childList:!0,subtree:!0});function a(n){const c={};return n.integrity&&(c.integrity=n.integrity),n.referrerPolicy&&(c.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?c.credentials="include":n.crossOrigin==="anonymous"?c.credentials="omit":c.credentials="same-origin",c}function s(n){if(n.ep)return;n.ep=!0;const c=a(n);fetch(n.href,c)}})();const G="";async function B(t){const e=await fetch(`${G}${t}`);if(!e.ok){const a=await e.json().catch(()=>({detail:e.statusText}));throw new Error(a.detail||e.statusText)}return e.json()}async function Q(t,e){const a=await fetch(`${G}${t}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok){const s=await a.json().catch(()=>({detail:a.statusText}));throw new Error(s.detail||a.statusText)}return a.json()}function W(t,e,a){const s=location.protocol==="https:"?"wss:":"ws:",n=new WebSocket(`${s}//${location.host}${t}`);return n.onmessage=c=>e(JSON.parse(c.data)),n.onerror=c=>a==null?void 0:a(c),n.onclose=()=>{setTimeout(()=>W(t,e,a),3e3)},n}const M={};let j=null;function $(t,e){M[t]=e}function p(t){if(j===t)return;j=t,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===t)});const e=document.getElementById("main-content");M[t]&&(e.innerHTML="",M[t](e)),history.replaceState(null,"",`#${t}`)}function Z(){const t=location.hash.replace("#","");return t&&M[t]?t:"ledger"}const i={contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:JSON.parse(localStorage.getItem("b60-scratch")||"[]"),databaseList:[],ledgerStats:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasOffset:{x:0,y:0},canvasScale:1};document.addEventListener("DOMContentLoaded",async()=>{u("indexing"),tt(),at(),it(),dt(),ut(),pt(),st(),mt(),await Promise.all([gt(),vt()]),R(),u("done");const t=localStorage.getItem("b60-route")||"ledger";U(t),p(Z()),u("idle")});function u(t){i.tachometerState=t;const e=document.getElementById("tachometer");if(!e)return;e.className=`tachometer ${t!=="idle"?t:""}`;const a=document.getElementById("status-agent-segment");if(a)if(t==="working"||t==="indexing"){a.style.display="flex";const s=document.getElementById("status-agent-text");s&&(s.textContent=t==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}function tt(){const t=document.getElementById("spine"),e=[{id:"canvas",icon:"⬡",tip:"Architecture Canvas  ⌘5"},{id:"ledger",icon:"⧉",tip:"BFT Ledger  ⌘1"},{id:"databases",icon:"⛁",tip:"Ontologies  ⌘2"},{id:"query",icon:"❯_",tip:"SQL Console  ⌘3"},{id:"swarm",icon:"⚡",tip:"Agent Swarm  ⌘4"}],a=e.map(c=>`<button class="spine-icon" data-route="${c.id}" data-tooltip="${c.tip}" aria-label="${c.tip}">${c.icon}</button>`).join(""),s='<div class="spine-separator"></div>';t.innerHTML=`
    <div class="spine-logo" title="BABYLON·60 v1.0.2">
      <div class="spine-logo-dot"></div>
    </div>
    ${a.slice(0,a.indexOf("</button>")+9)}
    ${s}
    ${a.slice(a.indexOf("</button>")+9)}
  `,t.innerHTML="";const n=document.createElement("div");n.className="spine-logo",n.title="BABYLON·60",n.innerHTML='<div class="spine-logo-dot"></div>',t.appendChild(n),e.forEach((c,o)=>{if(o===1){const r=document.createElement("div");r.className="spine-separator",t.appendChild(r)}const d=document.createElement("button");d.className="spine-icon",d.dataset.route=c.id,d.dataset.tooltip=c.tip,d.setAttribute("aria-label",c.tip),d.textContent=c.icon,d.addEventListener("click",()=>p(c.id)),t.appendChild(d)})}function et(t){document.querySelectorAll(".spine-icon").forEach(e=>{e.classList.toggle("active",e.dataset.route===t)})}function at(){const t=document.getElementById("btn-collapse-ctx");t&&t.addEventListener("click",P),_()}function P(){i.contextPaneOpen=!i.contextPaneOpen;const t=document.getElementById("context-pane"),e=document.getElementById("btn-collapse-ctx");t&&(t.classList.toggle("collapsed",!i.contextPaneOpen),e&&(e.textContent=i.contextPaneOpen?"⟨":"⟩"))}function _(){const t=document.getElementById("context-pane-body");t&&(t.innerHTML=`
    <div class="ctx-section">
      <div class="ctx-section-label">Inspector</div>
      <div class="ctx-item active" data-route="canvas">
        <span class="ctx-item-icon">⬡</span>
        <span class="ctx-item-label">Architecture</span>
        <span class="ctx-item-badge verify">live</span>
      </div>
      <div class="ctx-item" data-route="ledger">
        <span class="ctx-item-icon">⧉</span>
        <span class="ctx-item-label">BFT Ledger</span>
        <span class="ctx-item-badge gold" id="ctx-ledger-count">—</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">—</span>
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
        <span class="ctx-item-badge lapis" style="color:var(--lapis-bright)">0</span>
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Scratchpad</div>
      <div id="ctx-scratch-preview" style="padding:4px 12px; font-size:0.65rem; color:var(--dust-faint);">
        ${i.scratchpadItems.length===0?'<span style="color:var(--dust-ghost)">No notes yet</span>':`<span style="color:var(--dust-dim)">${i.scratchpadItems.length} note${i.scratchpadItems.length>1?"s":""}</span>`}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">System</div>
      <div class="ctx-item depth-1">
        <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
        <span class="ctx-item-label" style="font-size:0.65rem">master_ledger.db</span>
        <span class="ctx-item-badge verify">ok</span>
      </div>
      <div class="ctx-item depth-1">
        <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
        <span class="ctx-item-label" style="font-size:0.65rem">cortex_ontology.db</span>
        <span class="ctx-item-badge">RO</span>
      </div>
      <div class="ctx-item depth-1">
        <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
        <span class="ctx-item-label" style="font-size:0.65rem">telemetry.db</span>
        <span class="ctx-item-badge">RO</span>
      </div>
    </div>
  `,t.querySelectorAll(".ctx-item[data-route]").forEach(e=>{e.addEventListener("click",()=>p(e.dataset.route))}))}function J(){const t=document.getElementById("ctx-db-count");t&&(t.textContent=i.databaseList.length||"—");const e=document.getElementById("ctx-ledger-count");e&&i.ledgerStats&&(e.textContent=i.ledgerStats.total_entries||"—")}function nt(t){document.querySelectorAll(".ctx-item[data-route]").forEach(e=>{e.classList.toggle("active",e.dataset.route===t)})}function R(){var c,o;const t=document.getElementById("status-conn-dot"),e=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),s=document.getElementById("status-ledger-entries"),n=document.getElementById("status-lamport");t&&(t.className="status-dot"),e&&(e.textContent="CONNECTED"),a&&(a.textContent=i.databaseList.length||"—"),s&&(s.textContent=((c=i.ledgerStats)==null?void 0:c.total_entries)||"—"),n&&(n.textContent=((o=i.ledgerStats)==null?void 0:o.latest_lamport_t)!=null?`L:${i.ledgerStats.latest_lamport_t}`:"—")}function st(){const t=document.getElementById("btn-bifocal");t&&t.addEventListener("click",z)}function z(){i.bifocalMode=i.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",i.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",i.bifocalMode==="micro");const t=document.getElementById("btn-bifocal");t&&(t.textContent=i.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),i.bifocalMode==="macro"&&p("canvas")}const O=[{icon:"⬡",label:"Architecture Canvas",desc:"Macro system view",shortcut:"⌘5",action:()=>p("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"Hash-chain inspector",shortcut:"⌘1",action:()=>p("ledger")},{icon:"⛁",label:"Ontologies",desc:"SQLite database explorer",shortcut:"⌘2",action:()=>p("databases")},{icon:"❯_",label:"SQL Console",desc:"Read-only query interface",shortcut:"⌘3",action:()=>p("query")},{icon:"⚡",label:"Agent Swarm",desc:"Active agent telemetry",shortcut:"⌘4",action:()=>p("swarm")},{icon:"⬡",label:"Verify Chain Integrity",desc:"Run BFT hash-chain verification",shortcut:"",action:()=>{p("ledger"),setTimeout(()=>{var t;return(t=document.getElementById("btn-verify-chain"))==null?void 0:t.click()},400)}},{icon:"⟨",label:"Toggle Context Pane",desc:"Show / hide semantic map",shortcut:"⌘B",action:P},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Switch bifocal view mode",shortcut:"⌘M",action:z},{icon:"◎",label:"Open Scratchpad",desc:"Dump a thought (no focus loss)",shortcut:"⌘⇧Space",action:()=>I(!0)},{icon:"↺",label:"Restore Session",desc:"Return to last known context",shortcut:"",action:()=>U(localStorage.getItem("b60-route")||"ledger")}];let f=0,b=[...O];function it(){const t=document.getElementById("palette-overlay"),e=document.getElementById("palette-input");!t||!e||(t.addEventListener("click",a=>{a.target===t&&w()}),e.addEventListener("input",()=>ct(e.value)),e.addEventListener("keydown",rt))}function ot(){i.paletteOpen=!0;const t=document.getElementById("palette-overlay"),e=document.getElementById("palette-input");!t||!e||(t.classList.add("visible"),t.setAttribute("aria-hidden","false"),e.value="",f=0,b=[...O],D(),setTimeout(()=>e.focus(),50))}function w(){i.paletteOpen=!1;const t=document.getElementById("palette-overlay");t&&(t.classList.remove("visible"),t.setAttribute("aria-hidden","true"))}function ct(t){const e=t.toLowerCase().trim();f=0,e?b=O.filter(a=>a.label.toLowerCase().includes(e)||a.desc.toLowerCase().includes(e)):b=[...O],D(e)}function D(t=""){const e=document.getElementById("palette-results");if(e){if(b.length===0){e.innerHTML=`<div class="palette-empty">No commands match "<strong>${t}</strong>"</div>`;return}e.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${b.map((a,s)=>{const n=t?a.label.replace(new RegExp(`(${t})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${s===f?"selected":""}" data-index="${s}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${n}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,e.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const s=parseInt(a.dataset.index);b[s]&&(b[s].action(),w())}),a.addEventListener("mouseenter",()=>{f=parseInt(a.dataset.index),e.querySelectorAll(".palette-item").forEach((s,n)=>s.classList.toggle("selected",n===f))})})}}function rt(t){var e,a;if(t.key==="Escape"){w();return}t.key==="ArrowDown"&&(t.preventDefault(),f=Math.min(f+1,b.length-1),D(((e=document.getElementById("palette-input"))==null?void 0:e.value)||"")),t.key==="ArrowUp"&&(t.preventDefault(),f=Math.max(f-1,0),D(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),t.key==="Enter"&&(t.preventDefault(),b[f]&&(b[f].action(),w()))}function dt(){const t=document.getElementById("scratchpad-modal"),e=document.getElementById("scratchpad-input"),a=document.getElementById("scratchpad-save"),s=document.getElementById("scratchpad-close");!t||!e||(a==null||a.addEventListener("click",K),s==null||s.addEventListener("click",()=>I(!1)),e.addEventListener("keydown",n=>{n.key==="Enter"&&!n.shiftKey&&(n.preventDefault(),K()),n.key==="Escape"&&I(!1)}),F())}function I(t){const e=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");e&&(i.scratchpadOpen=t!==void 0?t:!i.scratchpadOpen,e.classList.toggle("visible",i.scratchpadOpen),e.setAttribute("aria-hidden",String(!i.scratchpadOpen)),i.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}function K(){const t=document.getElementById("scratchpad-input");if(!t||!t.value.trim())return;const e={id:Date.now(),text:t.value.trim(),time:new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})};i.scratchpadItems.unshift(e),i.scratchpadItems.length>20&&i.scratchpadItems.pop(),localStorage.setItem("b60-scratch",JSON.stringify(i.scratchpadItems)),t.value="",F(),_(),u("done"),setTimeout(()=>u("idle"),2e3)}function F(){const t=document.getElementById("scratchpad-items");if(t){if(i.scratchpadItems.length===0){t.innerHTML="";return}t.innerHTML=i.scratchpadItems.map(e=>`
    <div class="scratchpad-item" data-id="${e.id}">
      <span class="scratchpad-item-time">${e.time}</span>
      <span class="scratchpad-item-text">${e.text}</span>
      <span class="scratchpad-item-del" data-del="${e.id}" title="Remove">✕</span>
    </div>
  `).join(""),t.querySelectorAll("[data-del]").forEach(e=>{e.addEventListener("click",a=>{a.stopPropagation();const s=parseInt(e.dataset.del);i.scratchpadItems=i.scratchpadItems.filter(n=>n.id!==s),localStorage.setItem("b60-scratch",JSON.stringify(i.scratchpadItems)),F(),_()})})}}function lt({icon:t="⬡",message:e,actions:a=[]}){const s=document.getElementById("agent-modal"),n=document.getElementById("agent-modal-icon"),c=document.getElementById("agent-modal-msg"),o=document.getElementById("agent-modal-actions");if(!s||!c||!o)return;n&&(n.textContent=t),c.textContent=e;const d=[{label:"Got it",fn:k,primary:!0},{label:"Dismiss",fn:k}],r=a.length>0?a:d;o.innerHTML=r.map((l,m)=>`<button class="btn ${l.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${m}">${l.label}</button>`).join(""),o.querySelectorAll("button").forEach(l=>{l.addEventListener("click",()=>{var m,g;(g=(m=r[parseInt(l.dataset.actionIdx)])==null?void 0:m.fn)==null||g.call(m)})}),s.classList.add("visible"),s.setAttribute("aria-hidden","false"),u("alert")}function k(){const t=document.getElementById("agent-modal");t&&(t.classList.remove("visible"),t.setAttribute("aria-hidden","true")),u("idle")}function mt(){setInterval(()=>{if(!i.loopDetector.route||i.loopDetector.interventionFired)return;if(Date.now()-i.loopDetector.routeEnteredAt>1500*1e3){i.loopDetector.interventionFired=!0;const e=i.loopDetector.route;lt({icon:"⏱",message:`You've been in ${e.toUpperCase()} for over 25 minutes. Deep focus is good — but want to step back and see the whole system?`,actions:[{label:"Show Architecture",primary:!0,fn:()=>{k(),p("canvas")}},{label:"Keep Going",fn:k},{label:"Dump a thought →",fn:()=>{k(),I(!0)}}]})}},120*1e3)}function U(t){var d;const e=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),s=document.getElementById("restore-points"),n=document.getElementById("restore-dismiss");if(!e||!a)return;const o=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas"}[t]||t}`,`${i.databaseList.length||"—"} databases available`,(d=i.ledgerStats)!=null&&d.total_entries?`${i.ledgerStats.total_entries} ledger entries — chain intact`:"Ledger loading..."];a.textContent="Session restored · ",s&&(s.innerHTML=o.map(r=>`<span class="restore-point">${r}</span>`).join("")),e.style.display="flex",n==null||n.addEventListener("click",()=>{e.style.display="none"}),setTimeout(()=>{e.style.display="none"},12e3)}function ut(){const t={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas"};window.addEventListener("keydown",e=>{const a=e.metaKey||e.ctrlKey;if(a&&e.key==="k"&&!e.shiftKey){e.preventDefault(),i.paletteOpen?w():ot();return}if(a&&e.shiftKey&&e.code==="Space"){e.preventDefault(),I();return}if(a&&e.key==="b"&&!e.shiftKey){e.preventDefault(),P();return}if(a&&e.key==="m"&&!e.shiftKey){e.preventDefault(),z();return}if(a&&t[e.key]){e.preventDefault(),p(t[e.key]);return}if(e.key==="Escape"){if(i.paletteOpen){w();return}if(i.scratchpadOpen){I(!1);return}}})}function pt(){$("canvas",yt),$("ledger",ft),$("databases",bt),$("query",xt),$("swarm",Et),window.addEventListener("hashchange",()=>{const t=window.location.hash.replace("#","");t&&p(t)})}async function gt(){try{i.databaseList=await B("/api/databases"),J()}catch{}}async function vt(){try{i.ledgerStats=await B("/api/ledger/stats"),J(),R()}catch{}}function C({breadcrumb:t="",badge:e=null,actions:a=""}={}){const s=document.getElementById("focus-breadcrumb"),n=document.getElementById("focus-actions");s&&(s.innerHTML=t),n&&(n.innerHTML=a)}function T(...t){return t.map((e,a)=>a<t.length-1?`<span class="breadcrumb-item">${e}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${e}</span>`).join("")}function A(t){i.activeRoute=t,localStorage.setItem("b60-route",t),et(t),nt(t),i.loopDetector.route!==t&&(i.loopDetector.route=t,i.loopDetector.routeEnteredAt=Date.now(),i.loopDetector.interventionFired=!1)}async function yt(t){var d;A("canvas"),C({breadcrumb:T("BABYLON·60","Architecture"),actions:`
      <span style="font-size:0.6rem;color:var(--dust-faint)">Scroll to zoom · Drag to pan</span>
      <button class="btn btn-icon" id="canvas-fit" title="Fit to screen" style="margin-left:8px">⊞</button>
    `});const e=[{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"8 routes · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger DB",meta:"SHA3-256 · BFT chain",status:"ok"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Cortex Ontology",meta:"144MB · Read-only",status:"ok"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:"WebSocket · Live",status:"warn"},{id:"swarm",x:140,y:240,type:"AGENT",name:"Swarm Workers",meta:"0 active",status:"idle"},{id:"frontend",x:300,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:"Vite · Vanilla JS",status:"ok"}],a=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"swarm",to:"fastapi"},{from:"swarm",to:"ledger"}],s={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};t.innerHTML=`
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
  `;const n=document.getElementById("canvas-svg"),c=document.getElementById("canvas-edges"),o=document.getElementById("canvas-nodes");document.getElementById("canvas-main"),!(!n||!c||!o)&&(a.forEach(({from:r,to:l})=>{const m=e.find(L=>L.id===r),g=e.find(L=>L.id===l);if(!m||!g)return;const v=m.x+90,y=m.y+35,h=g.x,S=g.y+35,x=document.createElementNS("http://www.w3.org/2000/svg","path"),E=(v+h)/2;x.setAttribute("d",`M${v},${y} C${E},${y} ${E},${S} ${h},${S}`),x.setAttribute("stroke","var(--edge)"),x.setAttribute("stroke-width","1.5"),x.setAttribute("fill","none"),x.setAttribute("opacity","0.5"),x.setAttribute("marker-end","url(#arrow)"),c.appendChild(x)}),e.forEach(r=>{const l=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");l.setAttribute("x",r.x),l.setAttribute("y",r.y),l.setAttribute("width","180"),l.setAttribute("height","70");const m=document.createElement("div");m.className="canvas-node-card",m.style.position="relative",m.innerHTML=`
      <div class="canvas-node-type">${r.type}</div>
      <div class="canvas-node-name">${r.name}</div>
      <div class="canvas-node-meta">${r.meta}</div>
      <div class="canvas-node-status" style="background:${s[r.status]||s.idle};box-shadow:0 0 5px ${s[r.status]||s.idle}"></div>
    `,m.addEventListener("click",()=>{r.id==="ledger"?p("ledger"):r.id==="ontology"?p("databases"):r.id==="swarm"?p("swarm"):r.id==="fastapi"&&p("query")}),l.appendChild(m),o.appendChild(l)}),(d=document.getElementById("canvas-fit-btn"))==null||d.addEventListener("click",()=>{n.setAttribute("viewBox","80 50 700 380")}),n.setAttribute("viewBox","80 50 700 380"))}let H=1;const V=50;async function ft(t){var a,s,n,c,o,d;A("ledger"),C({breadcrumb:T("BABYLON·60","BFT Ledger"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),t.innerHTML=`
    <div class="stats-grid slide-in" id="ledger-stats-grid">
      <div class="stat-card">
        <div class="stat-label">Ledger File</div>
        <div class="stat-value lapis" id="stat-db-name" style="font-size:0.85rem">—</div>
        <div class="stat-sub">SQLite WAL</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Entries</div>
        <div class="stat-value gold" id="stat-total-entries">0</div>
        <div class="stat-sub" id="stat-latest-time">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Consensus</div>
        <div class="stat-value verify" id="stat-integrity">UNKNOWN</div>
        <div class="stat-sub" id="stat-latest-lamport">Lamport: —</div>
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title">Hash Chain Verification</div>
      </div>
      <div class="verify-progress" id="verify-progress-wrap" style="display:none">
        <div class="verify-progress-bar" id="verify-progress-bar"></div>
      </div>
      <div id="chain-visual-grid" class="chain-container">
        <div class="empty-state" style="padding:20px 0">
          <div class="icon">⚿</div>
          <div class="desc">Click "Verify Chain" to map blocks and assert BFT consensus.</div>
        </div>
      </div>
    </div>

    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ledger Sequence</div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Seq</th><th>Stream</th><th>Event Type</th>
              <th>Lamport T</th><th>Taint</th><th>Timestamp</th><th>Hash</th>
            </tr>
          </thead>
          <tbody id="ledger-table-body">
            <tr><td colspan="7" class="empty-state" style="text-align:center">Loading...</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button class="btn" id="btn-ledger-prev" disabled>◀ Prev</button>
        <span style="font-family:var(--font-mono);font-size:0.72rem" id="ledger-page-info">Page 1</span>
        <button class="btn" id="btn-ledger-next" disabled>Next ▶</button>
      </div>
    </div>

    <div id="entry-detail-panel" class="card" style="display:none;position:fixed;top:43px;right:0;width:440px;height:calc(100vh - 71px);border-radius:0;border-left:1px solid var(--edge);z-index:10;flex-direction:column;background:var(--kiln);transform:translateX(100%);transition:transform var(--t-slow)"></div>
  `;try{const r=await B("/api/ledger/stats");i.ledgerStats=r,(s=(a=document.getElementById("stat-db-name"))==null?void 0:a.let)==null||s.call(a,y=>{var h;return y.textContent=((h=r.db_path)==null?void 0:h.split("/").pop())||"master_ledger.db"});const l=document.getElementById("stat-db-name");l&&(l.textContent=((n=r.db_path)==null?void 0:n.split("/").pop())||"master_ledger.db");const m=document.getElementById("stat-total-entries");m&&(m.textContent=r.total_entries??0);const g=document.getElementById("stat-latest-lamport");g&&(g.textContent=`Lamport: ${r.latest_lamport_t??"—"}`);const v=document.getElementById("stat-latest-time");v&&r.latest_ts&&(v.textContent=r.latest_ts.slice(0,19)),R()}catch{}await q(1),(c=document.getElementById("btn-verify-chain"))==null||c.addEventListener("click",Y);const e=document.querySelector('[id="btn-verify-chain"]');e&&!e._wired&&(e._wired=!0,e.addEventListener("click",Y)),(o=document.getElementById("btn-ledger-prev"))==null||o.addEventListener("click",()=>q(H-1)),(d=document.getElementById("btn-ledger-next"))==null||d.addEventListener("click",()=>q(H+1))}async function q(t){H=t;const e=document.getElementById("ledger-table-body");if(e)try{const a=await B(`/api/ledger/entries?page=${t}&page_size=${V}`),s=Array.isArray(a)?a:a.entries||[];if(s.length===0){e.innerHTML='<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>';return}e.innerHTML=s.map(n=>`
      <tr class="${n.is_valid?"row-valid":"row-invalid"}" data-id="${n.id}" style="cursor:pointer">
        <td class="seq-cell">${n.id}</td>
        <td class="stream-cell">${n.stream_id??"—"}</td>
        <td>${n.event_type??"—"}</td>
        <td style="color:var(--dust-dim)">${n.lamport_t??"—"}</td>
        <td class="hash-cell" style="font-size:0.58rem">${(n.cortex_taint??"—").slice(0,16)}…</td>
        <td class="time-cell">${(n.ts??"").slice(0,19)}</td>
        <td class="hash-cell">${(n.curr_hash??"—").slice(0,12)}…</td>
      </tr>
    `).join(""),document.getElementById("ledger-page-info").textContent=`Page ${t}`,document.getElementById("btn-ledger-prev").disabled=t<=1,document.getElementById("btn-ledger-next").disabled=s.length<V}catch(a){e.innerHTML=`<tr><td colspan="7" style="text-align:center;color:var(--break)">Error: ${a.message}</td></tr>`}}async function Y(){const t=document.getElementById("btn-verify-chain"),e=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),s=document.getElementById("verify-progress-bar"),n=document.getElementById("stat-integrity");if(!e)return;t&&(t.disabled=!0,t.textContent="⚙ Verifying..."),a&&(a.style.display="block"),u("working");let c=0;const o=setInterval(()=>{c=Math.min(c+8,90),s&&(s.style.width=`${c}%`)},120);try{const d=await B("/api/ledger/verify");clearInterval(o),s&&(s.style.width="100%");const r=d.total_checked??0,l=d.valid_count??0,m=r-l,g=r>0?l/r:1;e.innerHTML="";for(let v=0;v<Math.min(r,200);v++){const y=document.createElement("div");y.className=`chain-block ${v<l?"":"invalid"}`,y.title=`Block ${v+1}: ${v<l?"VALID":"BROKEN"}`,e.appendChild(y)}n&&(n.textContent=g===1?"VERIFIED":`BROKEN (${m})`,n.className=`stat-value ${g===1?"verify":"break"}`),g===1?(u("done"),container.classList.add("reward-active"),setTimeout(()=>container.classList.remove("reward-active"),1500)):u("alert"),setTimeout(()=>u("idle"),3e3)}catch(d){clearInterval(o),e.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${d.message}</div>`,u("idle")}t&&(t.disabled=!1,t.textContent="⚿ Verify Chain"),a&&setTimeout(()=>a.style.display="none",1500)}async function bt(t){A("databases"),C({breadcrumb:T("BABYLON·60","Ontologies")}),t.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card">
        <div class="stat-label">SQLite Files</div>
        <div class="stat-value gold" id="db-total-count">${i.databaseList.length||"—"}</div>
        <div class="stat-sub">Discovered</div>
      </div>
    </div>
    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ontology Databases</div>
      <table class="data-table">
        <thead><tr><th>Database</th><th>Size</th><th>Type</th><th>Path</th></tr></thead>
        <tbody id="db-table-body"><tr><td colspan="4" style="text-align:center">Loading...</td></tr></tbody>
      </table>
    </div>
    <div class="card fade-in" style="margin-top:14px" id="db-schema-panel" style="display:none">
      <div class="card-title" id="db-schema-title">Schema</div>
      <div id="db-schema-body" style="font-family:var(--font-mono);font-size:0.7rem;color:var(--dust-dim)"></div>
    </div>
  `;try{const e=i.databaseList.length>0?i.databaseList:await B("/api/databases");i.databaseList=e;const a=document.getElementById("db-table-body"),s=document.getElementById("db-total-count");s&&(s.textContent=e.length);const n=o=>o>1e6?`${(o/1e6).toFixed(1)}MB`:`${(o/1024).toFixed(0)}KB`,c=o=>o.includes("ledger")?"LEDGER":o.includes("ontology")?"ONTOLOGY":o.includes("memory")||o.includes("cortex")?"CORTEX":o.includes("telemetry")?"TELEMETRY":"GENERAL";a&&(a.innerHTML=e.map(o=>`
      <tr style="cursor:pointer" data-path="${o.path}">
        <td class="stream-cell">${o.name}</td>
        <td class="time-cell">${o.size_bytes?n(o.size_bytes):"—"}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${c(o.name)}</span></td>
        <td class="hash-cell" style="font-size:0.6rem;max-width:320px">${o.path}</td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-path]").forEach(o=>{o.addEventListener("click",()=>{var d;return ht(o.dataset.path,(d=o.querySelector(".stream-cell"))==null?void 0:d.textContent)})})}catch(e){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="4" style="color:var(--break);text-align:center">${e.message}</td></tr>`)}}async function ht(t,e){var c;const a=document.getElementById("db-schema-panel"),s=document.getElementById("db-schema-title"),n=document.getElementById("db-schema-body");if(!(!a||!n)){a.style.display="block",s&&(s.textContent=`Schema — ${e}`),n.textContent="Loading schema...";try{const o=await Q("/api/databases/schema",{path:t});((c=o.tables)==null?void 0:c.length)>0?n.innerHTML=o.tables.map(d=>`
        <div style="margin-bottom:12px">
          <div style="color:var(--lapis-bright);font-weight:700;margin-bottom:4px">▸ ${d.name}</div>
          ${(d.columns||[]).map(r=>`<div style="padding-left:14px;color:var(--dust-faint)">${r.name} <span style="color:var(--dust-ghost)">${r.type}</span></div>`).join("")}
        </div>
      `).join(""):n.textContent="No tables found."}catch(o){n.innerHTML=`<span style="color:var(--break)">${o.message}</span>`}}}async function xt(t){var a,s,n,c;A("query"),C({breadcrumb:T("BABYLON·60","SQL Console")}),(a=i.databaseList[0])!=null&&a.path,t.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${i.databaseList.map(o=>`<option value="${o.path}">${o.name}</option>`).join("")}
        </select>
        <button class="btn btn-primary" id="btn-run-query">▶ Run</button>
        <button class="btn" id="btn-clear-query">Clear</button>
      </div>
      <div class="code-editor">
        <textarea id="query-input" placeholder="SELECT * FROM ledger_entries LIMIT 20;" spellcheck="false"></textarea>
        <div class="code-editor-toolbar">
          <span style="font-size:0.58rem;color:var(--dust-ghost)">Read-only · No DDL/DML</span>
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
  `;const e=async()=>{var g,v,y;const o=(v=(g=document.getElementById("query-input"))==null?void 0:g.value)==null?void 0:v.trim(),d=(y=document.getElementById("query-db-select"))==null?void 0:y.value;if(!o||!d)return;u("working");const r=document.getElementById("query-result-card"),l=document.getElementById("query-result-body"),m=document.getElementById("query-result-meta");r&&(r.style.display="block"),l&&(l.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const h=Date.now(),S=await Q("/api/query",{db_path:d,sql:o}),x=Date.now()-h,E=S.rows||[],L=S.columns||[];m&&(m.textContent=`${E.length} rows · ${x}ms`),l&&(E.length===0?l.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':l.innerHTML=`
            <table class="data-table">
              <thead><tr>${L.map(N=>`<th>${N}</th>`).join("")}</tr></thead>
              <tbody>${E.map(N=>`<tr>${L.map(X=>`<td>${N[X]??""}</td>`).join("")}</tr>`).join("")}</tbody>
            </table>
          `),u("done"),setTimeout(()=>u("idle"),2e3)}catch(h){l&&(l.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${h.message}</div>`),u("idle")}};(s=document.getElementById("btn-run-query"))==null||s.addEventListener("click",e),(n=document.getElementById("btn-clear-query"))==null||n.addEventListener("click",()=>{var d,r;const o=document.getElementById("query-input");o&&(o.value=""),(r=(d=document.getElementById("query-result-card"))==null?void 0:d.style)==null||r.setProperty("display","none")}),(c=document.getElementById("query-input"))==null||c.addEventListener("keydown",o=>{o.shiftKey&&o.key==="Enter"&&(o.preventDefault(),e())})}async function Et(t){var a,s;A("swarm"),C({breadcrumb:T("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'});const e=[{name:"MOSKV-1 APEX",status:"idle",task:"Awaiting directive",progress:0},{name:"BFT Verifier",status:"done",task:"Chain verified: 100%",progress:100},{name:"Context Indexer",status:"idle",task:"Index up to date",progress:100}];t.innerHTML=`
    <div class="swarm-layout">
      <div class="swarm-terminal">
        <div class="swarm-terminal-header">
          <div class="status-dot" style="width:5px;height:5px;border-radius:50%;background:var(--verify)"></div>
          Agentic Log
        </div>
        <div class="swarm-terminal-body" id="swarm-log-body">
          <div class="swarm-log-line"><span class="swarm-log-time">—:—</span><span class="swarm-log-agent">SYSTEM</span><span class="swarm-log-msg">Waiting for WebSocket stream...</span></div>
        </div>
      </div>
      <div class="swarm-inspector">
        <div class="swarm-inspector-header">Agent State</div>
        <div class="swarm-inspector-body">
          ${e.map(n=>`
            <div class="agent-card">
              <div class="agent-card-header">
                <span class="agent-name">${n.name}</span>
                <span class="agent-status-pill ${n.status}">${n.status.toUpperCase()}</span>
              </div>
              <div class="agent-task">${n.task}</div>
              <div class="agent-progress">
                <div class="agent-progress-fill ${n.status==="done"?"done":""}" style="width:${n.progress}%"></div>
              </div>
            </div>
          `).join("")}
        </div>
      </div>
    </div>
  `,i.telemetrySocket&&((s=(a=i.telemetrySocket).close)==null||s.call(a)),u("indexing"),i.telemetrySocket=W("/ws/telemetry",n=>{Lt(n)},()=>{u("idle")})}function Lt(t){const e=document.getElementById("swarm-log-body");if(!e)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),s=document.createElement("div");s.className="swarm-log-line";const n=t.level||"info";s.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">${t.agent||"SYSTEM"}</span>
    <span class="swarm-log-msg ${n}">${t.message||JSON.stringify(t)}</span>
  `,e.appendChild(s),e.scrollTop=e.scrollHeight,i.swarmLog.push({time:a,...t})}
