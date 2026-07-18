(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))l(s);new MutationObserver(s=>{for(const i of s)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&l(o)}).observe(document,{childList:!0,subtree:!0});function a(s){const i={};return s.integrity&&(i.integrity=s.integrity),s.referrerPolicy&&(i.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?i.credentials="include":s.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function l(s){if(s.ep)return;s.ep=!0;const i=a(s);fetch(s.href,i)}})();const we="";async function w(e){const t=await fetch(`${we}${e}`);if(!t.ok){const a=await t.json().catch(()=>({detail:t.statusText}));throw new Error(a.detail||t.statusText)}return t.json()}async function Le(e,t){const a=await fetch(`${we}${e}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok){const l=await a.json().catch(()=>({detail:a.statusText}));throw new Error(l.detail||a.statusText)}return a.json()}function Ae(e,t,a){const l=location.protocol==="https:"?"wss:":"ws:",s={closed:!1,ws:null},i=()=>{if(s.closed)return;const o=new WebSocket(`${l}//${location.host}${e}`);s.ws=o,o.onmessage=c=>{let r;try{r=JSON.parse(c.data)}catch{return}t(r)},o.onerror=c=>a==null?void 0:a(c),o.onclose=()=>{s.closed||setTimeout(i,3e3)}};return s.close=()=>{var o;s.closed=!0;try{(o=s.ws)==null||o.close()}catch{}},i(),s}const O={};let z=null;function M(e,t){O[e]=t}function b(e){if(z===e)return;z=e,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===e)});const t=document.getElementById("main-content");O[e]&&(t.innerHTML="",O[e](t)),history.replaceState(null,"",`#${e}`)}function Se(){const e=document.getElementById("main-content");z&&O[z]&&e&&(e.innerHTML="",O[z](e))}function Ce(){const e=location.hash.replace("#","");return e&&O[e]?e:"ledger"}const X={"2e":{key:"2e",label:"2E ◐",name:"Doble Excepcionalidad (TDAH + AACC)",tachometer:!0,loopGuard:!0,restoreBanner:!0,rewards:!0,spineLabels:!1},nt:{key:"nt",label:"NT ○",name:"Neurotípico",tachometer:!1,loopGuard:!1,restoreBanner:!1,rewards:!1,spineLabels:!0}};function E(){return X[n.cognitiveMode]||X["2e"]}function Ee(e){try{const t=JSON.parse(e||"[]");return Array.isArray(t)?t:[]}catch{return[]}}const n={cognitiveMode:localStorage.getItem("b60-cogmode")||"2e",contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:Ee(localStorage.getItem("b60-scratch")),delegationQueue:Ee(localStorage.getItem("b60-delegation")),databaseList:[],ledgerStats:null,lastVerify:null,sentinel:null,sentinelModalShown:!1,telemetrySnapshot:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasVB:{x:80,y:40,w:720,h:400},canvasAbort:null};document.addEventListener("DOMContentLoaded",async()=>{Ie(n.cognitiveMode,{silent:!0}),f("indexing"),Be(),_e(),Ne(),Ve(),Qe(),Ye(),He(),Me(),Ge(),await Promise.all([ke(),Ke(),De()]),ne(),P(),f("done"),E().restoreBanner&&Fe(localStorage.getItem("b60-route")||"ledger"),b(Ce()),f("idle")});function Ie(e,{silent:t=!1}={}){n.cognitiveMode=X[e]?e:"2e",localStorage.setItem("b60-cogmode",n.cognitiveMode),document.body.classList.toggle("mode-2e",n.cognitiveMode==="2e"),document.body.classList.toggle("mode-nt",n.cognitiveMode==="nt");const a=document.getElementById("btn-cogmode");a&&(a.textContent=E().label,a.title=`Modo cognitivo: ${E().name} — click o ⌘⇧E para alternar`),t||(Be(),Se(),Y({icon:E().key==="2e"?"◐":"○",message:`Modo cognitivo: ${E().name}. ${E().key==="2e"?"Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos.":"Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."}`}),setTimeout(I,3e3))}function te(){Ie(n.cognitiveMode==="2e"?"nt":"2e")}function Me(){var t;let e=document.getElementById("btn-cogmode");if(!e){const a=(t=document.getElementById("btn-bifocal"))==null?void 0:t.parentElement;if(a){const l=document.createElement("div");l.className="status-segment",l.innerHTML='<button class="status-bifocal" id="btn-cogmode"></button>',a.parentElement.insertBefore(l,a),e=l.querySelector("#btn-cogmode")}}e&&(e.textContent=E().label,e.title=`Modo cognitivo: ${E().name} — click o ⌘⇧E para alternar`,e.addEventListener("click",te))}function f(e){n.tachometerState=e;const t=document.getElementById("tachometer");t&&(t.className=`tachometer ${e!=="idle"?e:""}`);const a=document.getElementById("status-agent-segment");if(a)if(e==="working"||e==="indexing"){a.style.display="flex";const l=document.getElementById("status-agent-text");l&&(l.textContent=e==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}const Oe=[{id:"canvas",icon:"⬡",label:"Canvas",tip:"Architecture Canvas — ABSTRAER  ⌘5"},{id:"ledger",icon:"⧉",label:"Ledger",tip:"BFT Ledger — DETERMINAR  ⌘1"},{id:"databases",icon:"⛁",label:"Ontologies",tip:"Ontologies (explorador SQLite)  ⌘2"},{id:"query",icon:"❯_",label:"SQL",tip:"SQL Console (solo lectura)  ⌘3"},{id:"swarm",icon:"⚡",label:"Swarm",tip:"Agent Swarm (telemetría en vivo)  ⌘4"},{id:"sentinel",icon:"⎇",label:"Sentinel",tip:"Git Sentinel (identidad de repo + delegación)  ⌘6"}];function Be(){const e=document.getElementById("spine");if(!e)return;e.innerHTML="";const t=document.createElement("div");t.className="spine-logo",t.title="BABYLON·60 v1.1.0",t.innerHTML='<div class="spine-logo-dot"></div>',e.appendChild(t);const a=E().spineLabels;Oe.forEach((l,s)=>{if(s===1){const o=document.createElement("div");o.className="spine-separator",e.appendChild(o)}const i=document.createElement("button");i.className="spine-icon",i.dataset.route=l.id,a||(i.dataset.tooltip=l.tip),i.setAttribute("aria-label",l.tip),i.innerHTML=a?`<span class="spine-glyph">${l.icon}</span><span class="spine-label">${l.label}</span>`:l.icon,i.addEventListener("click",()=>b(l.id)),e.appendChild(i)}),Te(n.activeRoute)}function Te(e){document.querySelectorAll(".spine-icon").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function _e(){var e;(e=document.getElementById("btn-collapse-ctx"))==null||e.addEventListener("click",ae),P()}function ae(){n.contextPaneOpen=!n.contextPaneOpen;const e=document.getElementById("context-pane"),t=document.getElementById("btn-collapse-ctx");e&&(e.classList.toggle("collapsed",!n.contextPaneOpen),t&&(t.textContent=n.contextPaneOpen?"⟨":"⟩"))}function P(){var l,s,i,o,c;const e=document.getElementById("context-pane-body");if(!e)return;const t=n.databaseList.slice(0,5).map(r=>`
    <div class="ctx-item depth-1" data-goto-db="${d(r.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${d(r.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `).join(""),a=(s=(l=n.sentinel)==null?void 0:l.warnings)!=null&&s.some(r=>r.level==="red")?'<span class="ctx-item-badge break">!</span>':(o=(i=n.sentinel)==null?void 0:i.warnings)!=null&&o.length?'<span class="ctx-item-badge gold">△</span>':'<span class="ctx-item-badge verify">ok</span>';e.innerHTML=`
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
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${((c=n.ledgerStats)==null?void 0:c.entries)??"—"}</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">${n.databaseList.length||"—"}</span>
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
        ${n.scratchpadItems.length===0?'<span style="color:var(--dust-ghost)">No notes yet</span>':`<span style="color:var(--dust-dim)">${n.scratchpadItems.length} note${n.scratchpadItems.length>1?"s":""}</span>`}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Databases</div>
      ${t||'<div style="padding:4px 12px;font-size:0.62rem;color:var(--dust-ghost)">No .db discovered</div>'}
    </div>
  `,e.querySelectorAll(".ctx-item[data-route]").forEach(r=>{r.addEventListener("click",()=>b(r.dataset.route))}),e.querySelectorAll(".ctx-item[data-goto-db]").forEach(r=>{r.addEventListener("click",()=>b("databases"))})}function Q(){var a;const e=document.getElementById("ctx-db-count");e&&(e.textContent=n.databaseList.length||"—");const t=document.getElementById("ctx-ledger-count");t&&(t.textContent=((a=n.ledgerStats)==null?void 0:a.entries)??"—")}function qe(e){document.querySelectorAll(".ctx-item[data-route]").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function ne(){var o,c,r;const e=document.getElementById("status-conn-dot"),t=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),l=document.getElementById("status-ledger-entries"),s=document.getElementById("status-lamport"),i=n.ledgerStats!==null||n.databaseList.length>0;e&&(e.className=i?"status-dot":"status-dot error"),t&&(t.textContent=i?"CONNECTED":"OFFLINE"),a&&(a.textContent=n.databaseList.length||"—"),l&&(l.textContent=((o=n.ledgerStats)==null?void 0:o.entries)??"—"),s&&(s.textContent=((r=(c=n.ledgerStats)==null?void 0:c.latest)==null?void 0:r.lamport_t)!=null?`L:${n.ledgerStats.latest.lamport_t}`:"—"),se()}function se(){var i,o;let e=document.getElementById("status-repo-segment");if(!e){const c=document.getElementById("status-bar"),r=c==null?void 0:c.querySelector(".status-segment");if(!c||!r)return;e=document.createElement("div"),e.className="status-segment",e.id="status-repo-segment",e.style.cursor="pointer",e.innerHTML='<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>',r.after(e),e.addEventListener("click",()=>b("sentinel"))}const t=document.getElementById("status-repo-text");if(!t)return;const a=n.sentinel;if(!a){t.textContent="—";return}const l=(i=a.warnings)==null?void 0:i.some(c=>c.level==="red"),s=!l&&((o=a.warnings)==null?void 0:o.length)>0;t.textContent=`${a.repo_name}${a.branch?" @"+a.branch:""}${a.head?" · "+a.head:""}${l?" ⚠":s?" △":" ✓"}`,t.style.color=l?"var(--break)":s?"var(--gold)":"var(--verify)",e.title=l?"LINAJE NO CANÓNICO — abre Git Sentinel":s?"Avisos de linaje — abre Git Sentinel":`Linaje canónico verificado (${a.commit_count??"—"} commits)`}async function De(){var e;try{n.sentinel=await w("/api/sentinel/status"),se();const t=((e=n.sentinel.warnings)==null?void 0:e.filter(a=>a.level==="red"))||[];t.length>0&&!n.sentinelModalShown&&(n.sentinelModalShown=!0,Y({icon:"⚠",message:`GIT SENTINEL: ${t[0].msg}`,actions:[{label:"Abrir Sentinel",primary:!0,fn:()=>{I(),b("sentinel")}},{label:"Entendido",fn:I}]}))}catch{}}function He(){var e;(e=document.getElementById("btn-bifocal"))==null||e.addEventListener("click",ie)}function ie(){n.bifocalMode=n.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",n.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",n.bifocalMode==="micro");const e=document.getElementById("btn-bifocal");e&&(e.textContent=n.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),n.bifocalMode==="macro"&&b("canvas")}const V=[{icon:"⬡",label:"Architecture Canvas",desc:"ABSTRAER: ver el sistema completo",shortcut:"⌘5",action:()=>b("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"DETERMINAR: inspector de cadena de hashes",shortcut:"⌘1",action:()=>b("ledger")},{icon:"⛁",label:"Ontologies",desc:"Explorador SQLite (solo lectura)",shortcut:"⌘2",action:()=>b("databases")},{icon:"❯_",label:"SQL Console",desc:"Consultas read-only contra cualquier .db",shortcut:"⌘3",action:()=>b("query")},{icon:"⚡",label:"Agent Swarm",desc:"Telemetría en vivo (push WS, sin polling)",shortcut:"⌘4",action:()=>b("swarm")},{icon:"⎇",label:"Git Sentinel",desc:"Identidad de repo + delegación de mutaciones git",shortcut:"⌘6",action:()=>b("sentinel")},{icon:"⚿",label:"Verify Chain Integrity",desc:"Recomputar SHA3-256 de toda la cadena",shortcut:"",action:()=>{b("ledger"),setTimeout(()=>{var e;return(e=document.getElementById("btn-verify-chain"))==null?void 0:e.click()},400)}},{icon:"◐",label:"Toggle Cognitive Mode",desc:"Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",shortcut:"⌘⇧E",action:te},{icon:"⟨",label:"Toggle Context Pane",desc:"Mostrar / ocultar mapa semántico",shortcut:"⌘B",action:ae},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Alternar vista bifocal",shortcut:"⌘M",action:ie},{icon:"◎",label:"Open Scratchpad",desc:"Volcar un pensamiento sin perder foco",shortcut:"⌘⇧Space",action:()=>q(!0)}];let S=0,B=[...V];function Ne(){const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.addEventListener("click",a=>{a.target===e&&_()}),t.addEventListener("input",()=>ze(t.value)),t.addEventListener("keydown",je))}function Re(){n.paletteOpen=!0;const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.classList.add("visible"),e.setAttribute("aria-hidden","false"),t.value="",S=0,B=[...V],G(),setTimeout(()=>t.focus(),50))}function _(){n.paletteOpen=!1;const e=document.getElementById("palette-overlay");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true"))}function ze(e){const t=e.toLowerCase().trim();S=0,B=t?V.filter(a=>a.label.toLowerCase().includes(t)||a.desc.toLowerCase().includes(t)):[...V],G(t)}function Pe(e){return e.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}function G(e=""){const t=document.getElementById("palette-results");if(t){if(B.length===0){t.innerHTML=`<div class="palette-empty">No commands match "<strong>${d(e)}</strong>"</div>`;return}t.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${B.map((a,l)=>{const s=e?a.label.replace(new RegExp(`(${Pe(e)})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${l===S?"selected":""}" data-index="${l}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${s}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,t.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const l=parseInt(a.dataset.index);B[l]&&(B[l].action(),_())}),a.addEventListener("mouseenter",()=>{S=parseInt(a.dataset.index),t.querySelectorAll(".palette-item").forEach((l,s)=>l.classList.toggle("selected",s===S))})})}}function je(e){var t,a;if(e.key==="Escape"){_();return}e.key==="ArrowDown"&&(e.preventDefault(),S=Math.min(S+1,B.length-1),G(((t=document.getElementById("palette-input"))==null?void 0:t.value)||"")),e.key==="ArrowUp"&&(e.preventDefault(),S=Math.max(S-1,0),G(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),e.key==="Enter"&&(e.preventDefault(),B[S]&&(B[S].action(),_()))}function Ve(){var a,l;const e=document.getElementById("scratchpad-modal"),t=document.getElementById("scratchpad-input");!e||!t||((a=document.getElementById("scratchpad-save"))==null||a.addEventListener("click",xe),(l=document.getElementById("scratchpad-close"))==null||l.addEventListener("click",()=>q(!1)),t.addEventListener("keydown",s=>{s.key==="Enter"&&!s.shiftKey&&(s.preventDefault(),xe()),s.key==="Escape"&&q(!1)}),oe())}function q(e){const t=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");t&&(n.scratchpadOpen=e!==void 0?e:!n.scratchpadOpen,t.classList.toggle("visible",n.scratchpadOpen),t.setAttribute("aria-hidden",String(!n.scratchpadOpen)),n.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}function xe(){const e=document.getElementById("scratchpad-input");if(!e||!e.value.trim())return;const t={id:Date.now(),text:e.value.trim(),time:new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})};n.scratchpadItems.unshift(t),n.scratchpadItems.length>20&&n.scratchpadItems.pop(),localStorage.setItem("b60-scratch",JSON.stringify(n.scratchpadItems)),e.value="",oe(),P(),E().rewards&&(f("done"),setTimeout(()=>f("idle"),2e3))}function oe(){const e=document.getElementById("scratchpad-items");if(e){if(n.scratchpadItems.length===0){e.innerHTML="";return}e.innerHTML=n.scratchpadItems.map(t=>`
    <div class="scratchpad-item" data-id="${t.id}">
      <span class="scratchpad-item-time">${t.time}</span>
      <span class="scratchpad-item-text">${d(t.text)}</span>
      <span class="scratchpad-item-del" data-del="${t.id}" title="Remove">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",a=>{a.stopPropagation();const l=parseInt(t.dataset.del);n.scratchpadItems=n.scratchpadItems.filter(s=>s.id!==l),localStorage.setItem("b60-scratch",JSON.stringify(n.scratchpadItems)),oe(),P()})})}}function Y({icon:e="⬡",message:t,actions:a=[]}){const l=document.getElementById("agent-modal"),s=document.getElementById("agent-modal-icon"),i=document.getElementById("agent-modal-msg"),o=document.getElementById("agent-modal-actions");if(!l||!i||!o)return;s&&(s.textContent=e),i.textContent=t;const c=a.length>0?a:[{label:"Got it",fn:I,primary:!0}];o.innerHTML=c.map((r,m)=>`<button class="btn ${r.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${m}">${r.label}</button>`).join(""),o.querySelectorAll("button").forEach(r=>{r.addEventListener("click",()=>{var m,u;return(u=(m=c[parseInt(r.dataset.actionIdx)])==null?void 0:m.fn)==null?void 0:u.call(m)})}),l.classList.add("visible"),l.setAttribute("aria-hidden","false"),E().tachometer&&f("alert")}function I(){const e=document.getElementById("agent-modal");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true")),f("idle")}function Ge(){setInterval(()=>{if(!E().loopGuard||!n.loopDetector.route||n.loopDetector.interventionFired)return;if(Date.now()-n.loopDetector.routeEnteredAt>1500*1e3){n.loopDetector.interventionFired=!0;const t=n.loopDetector.route;Y({icon:"⏱",message:`Llevas más de 25 minutos en ${t.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,actions:[{label:"Ver Arquitectura",primary:!0,fn:()=>{I(),b("canvas")}},{label:"Sigo aquí",fn:I},{label:"Volcar idea →",fn:()=>{I(),q(!0)}}]})}},120*1e3)}function Fe(e){var c;const t=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),l=document.getElementById("restore-points"),s=document.getElementById("restore-dismiss");if(!t||!a)return;const o=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas",sentinel:"Git Sentinel"}[e]||e}`,`${n.databaseList.length||"—"} databases available`,((c=n.ledgerStats)==null?void 0:c.entries)!=null?`${n.ledgerStats.entries} ledger entries`:"Ledger loading...",n.sentinel?`repo ${n.sentinel.repo_name}@${n.sentinel.branch??"—"}`:""].filter(Boolean);a.textContent="Session restored · ",l&&(l.innerHTML=o.map(r=>`<span class="restore-point">${d(r)}</span>`).join("")),t.style.display="flex",s==null||s.addEventListener("click",()=>{t.style.display="none"}),setTimeout(()=>{t.style.display="none"},12e3)}function Qe(){const e={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas",6:"sentinel"};window.addEventListener("keydown",t=>{const a=t.metaKey||t.ctrlKey;if(a&&t.key==="k"&&!t.shiftKey){t.preventDefault(),n.paletteOpen?_():Re();return}if(a&&t.shiftKey&&t.code==="Space"){t.preventDefault(),q();return}if(a&&t.shiftKey&&(t.key==="e"||t.key==="E")){t.preventDefault(),te();return}if(a&&t.key==="b"&&!t.shiftKey){t.preventDefault(),ae();return}if(a&&t.key==="m"&&!t.shiftKey){t.preventDefault(),ie();return}if(a&&e[t.key]){t.preventDefault(),b(e[t.key]);return}if(t.key==="Escape"){if(n.paletteOpen){_();return}if(n.scratchpadOpen){q(!1);return}F()}})}function Ye(){M("canvas",Ue),M("ledger",We),M("databases",Xe),M("query",tt),M("swarm",at),M("sentinel",it),window.addEventListener("hashchange",()=>{const e=window.location.hash.replace("#","");e&&b(e)})}async function ke(){try{n.databaseList=await w("/api/databases"),Q()}catch{}}async function Ke(){try{n.ledgerStats=await w("/api/ledger/stats"),Q(),ne()}catch{}}function T({breadcrumb:e="",actions:t=""}={}){const a=document.getElementById("focus-breadcrumb"),l=document.getElementById("focus-actions");a&&(a.innerHTML=e),l&&(l.innerHTML=t)}function k(...e){return e.map((t,a)=>a<e.length-1?`<span class="breadcrumb-item">${t}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${t}</span>`).join("")}function D(e){n.activeRoute=e,localStorage.setItem("b60-route",e),Te(e),qe(e),F(),e!=="swarm"&&n.telemetrySocket&&(n.telemetrySocket.close(),n.telemetrySocket=null),n.loopDetector.route!==e&&(n.loopDetector.route=e,n.loopDetector.routeEnteredAt=Date.now(),n.loopDetector.interventionFired=!1)}function d(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Ue(e){var re,de,ce,me,ue,pe,ge;D("canvas"),T({breadcrumb:k("BABYLON·60","Architecture — ABSTRAER (ver el todo antes que la parte)"),actions:'<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>'});try{n.telemetrySnapshot=await w("/api/telemetry/snapshot")}catch{}const t=n.telemetrySnapshot,a=n.databaseList.length,l=((re=n.ledgerStats)==null?void 0:re.entries)??"—",s=(t==null?void 0:t.total_db_size_mb)!=null?`${t.total_db_size_mb}MB`:"—",i=n.sentinel,o=i!=null&&i.is_git?`${i.repo_name}@${i.branch??"—"} · ${i.head??"—"}`:"no git",c=(de=i==null?void 0:i.warnings)!=null&&de.some(p=>p.level==="red")?"err":(ce=i==null?void 0:i.warnings)!=null&&ce.length?"warn":"ok",r=[{id:"frontend",x:140,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:`Vite · modo ${E().key.toUpperCase()}`,status:"ok"},{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"14 endpoints · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger",meta:`${l} entries · SHA3-256 (huella criptográfica)`,status:(me=n.ledgerStats)!=null&&me.exists?"ok":"err",goto:"ledger"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Ontology DBs",meta:`${a} DBs · ${s} · RO`,status:a>0?"ok":"warn",goto:"databases"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:t?"WS push 2s (sin polling)":"offline",status:t?"ok":"warn",goto:"swarm"},{id:"git",x:140,y:240,type:"SENTINEL",name:"Git Sentinel",meta:o,status:c,goto:"sentinel"}],m=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"git",to:"fastapi"}],u={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};e.innerHTML=`
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
  `;const y=document.getElementById("canvas-svg"),h=document.getElementById("canvas-edges"),g=document.getElementById("canvas-nodes");if(!y||!h||!g)return;m.forEach(({from:p,to:v})=>{const L=r.find(U=>U.id===p),R=r.find(U=>U.id===v);if(!L||!R)return;const ve=L.x+90,ye=L.y+35,fe=R.x,be=R.y+35,C=document.createElementNS("http://www.w3.org/2000/svg","path"),he=(ve+fe)/2;C.setAttribute("d",`M${ve},${ye} C${he},${ye} ${he},${be} ${fe},${be}`),C.setAttribute("stroke","var(--edge)"),C.setAttribute("stroke-width","1.5"),C.setAttribute("fill","none"),C.setAttribute("opacity","0.5"),C.setAttribute("marker-end","url(#arrow)"),h.appendChild(C)}),r.forEach(p=>{const v=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");v.setAttribute("x",p.x),v.setAttribute("y",p.y),v.setAttribute("width","195"),v.setAttribute("height","76");const L=document.createElement("div");L.className="canvas-node-card",L.style.position="relative",L.innerHTML=`
      <div class="canvas-node-type">${p.type}</div>
      <div class="canvas-node-name">${p.name}</div>
      <div class="canvas-node-meta">${d(p.meta)}</div>
      <div class="canvas-node-status" style="background:${u[p.status]||u.idle};box-shadow:0 0 5px ${u[p.status]||u.idle}"></div>
    `,p.goto&&L.addEventListener("click",()=>b(p.goto)),v.appendChild(L),g.appendChild(v)});const $=()=>y.setAttribute("viewBox",`${n.canvasVB.x} ${n.canvasVB.y} ${n.canvasVB.w} ${n.canvasVB.h}`),H=()=>{n.canvasVB={x:80,y:40,w:720,h:400},$()};H();const A=p=>{const v=n.canvasVB,L=v.x+v.w/2,R=v.y+v.h/2;v.w=Math.max(200,Math.min(2e3,v.w*p)),v.h=Math.max(110,Math.min(1100,v.h*p)),v.x=L-v.w/2,v.y=R-v.h/2,$()};(ue=document.getElementById("canvas-zoom-in"))==null||ue.addEventListener("click",()=>A(1/1.2)),(pe=document.getElementById("canvas-zoom-out"))==null||pe.addEventListener("click",()=>A(1.2)),(ge=document.getElementById("canvas-fit-btn"))==null||ge.addEventListener("click",H),y.addEventListener("wheel",p=>{p.preventDefault(),A(p.deltaY>0?1.1:1/1.1)},{passive:!1}),n.canvasAbort&&n.canvasAbort.abort(),n.canvasAbort=new AbortController;const j=n.canvasAbort.signal;let x=!1,N=0,K=0;y.addEventListener("pointerdown",p=>{x=!0,N=p.clientX,K=p.clientY}),window.addEventListener("pointermove",p=>{if(!x)return;const v=n.canvasVB.w/y.clientWidth;n.canvasVB.x-=(p.clientX-N)*v,n.canvasVB.y-=(p.clientY-K)*v,N=p.clientX,K=p.clientY,$()},{signal:j}),window.addEventListener("pointerup",()=>{x=!1},{signal:j})}let Z=1;const W=50;async function We(e){var t,a,l,s,i;D("ledger"),T({breadcrumb:k("BABYLON·60","BFT Ledger — DETERMINAR (verificar hasta el hash)"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),(t=document.getElementById("btn-verify-chain"))==null||t.addEventListener("click",Je),e.innerHTML=`
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
  `;try{const o=await w("/api/ledger/stats");n.ledgerStats=o;const c=document.getElementById("stat-db-name");c&&(c.textContent=o.db_path||"—");const r=document.getElementById("stat-total-entries");r&&(r.textContent=o.entries??0);const m=document.getElementById("stat-latest-lamport");m&&(m.textContent=`Lamport (reloj lógico causal): ${((a=o.latest)==null?void 0:a.lamport_t)??"—"}`);const u=document.getElementById("stat-latest-time");u&&((l=o.latest)!=null&&l.created_at)&&(u.textContent=String(o.latest.created_at).slice(0,19)),ne(),Q()}catch{}await J(1),(s=document.getElementById("btn-ledger-prev"))==null||s.addEventListener("click",()=>J(Z-1)),(i=document.getElementById("btn-ledger-next"))==null||i.addEventListener("click",()=>J(Z+1))}async function J(e){e<1&&(e=1),Z=e;const t=document.getElementById("ledger-table-body");if(t)try{const a=(e-1)*W,l=await w(`/api/ledger/entries?limit=${W}&offset=${a}`),s=l.entries||[],i=l.total??s.length;s.length===0?t.innerHTML='<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>':(t.innerHTML=s.map(u=>`
        <tr data-seq="${u.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${u.seq}</td>
          <td class="stream-cell">${d(u.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${d(u.entity_id)}</td>
          <td>${d(u.event_type)}</td>
          <td style="color:var(--dust-dim)">${u.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${d(u.cortex_taint)}">${d((u.cortex_taint||"—").slice(0,26))}${(u.cortex_taint||"").length>26?"…":""}</td>
          <td class="time-cell">${String(u.created_at||"").slice(0,19)}</td>
          <td class="hash-cell" title="${d(u.entry_hash)}">${(u.entry_hash||"—").slice(0,12)}…</td>
        </tr>
      `).join(""),t.querySelectorAll("tr[data-seq]").forEach(u=>{u.addEventListener("click",()=>ee(parseInt(u.dataset.seq)))}));const o=Math.max(1,Math.ceil(i/W)),c=document.getElementById("ledger-page-info");c&&(c.textContent=`Page ${e} / ${o} · ${i} entries`);const r=document.getElementById("btn-ledger-prev"),m=document.getElementById("btn-ledger-next");r&&(r.disabled=e<=1),m&&(m.disabled=e>=o)}catch(a){t.innerHTML=`<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${d(a.message)}</td></tr>`}}async function ee(e){var a,l;const t=document.getElementById("entry-detail-panel");if(t){t.classList.add("open"),t.setAttribute("aria-hidden","false"),t.innerHTML=`<div class="detail-header"><span class="detail-title">⧉ Entry #${e}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`,(a=t.querySelector("#detail-close"))==null||a.addEventListener("click",F);try{const s=await w(`/api/ledger/entry/${e}`);let i=s.payload_json||"";try{i=JSON.stringify(JSON.parse(s.payload_json),null,2)}catch{}const o=(c,r,m="")=>`
      <div class="detail-field">
        <div class="detail-field-label">${c}</div>
        <div class="detail-field-value ${m}">${d(r??"—")}</div>
      </div>`;t.innerHTML=`
      <div class="detail-header">
        <span class="detail-title">⧉ Entry #${s.seq} · ${d(s.event_type)}</span>
        <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button>
      </div>
      <div class="detail-body">
        ${o("Event ID (UUID v5: determinista, mismo input → mismo id)",s.event_id,"mono")}
        ${o("Stream · Entity",`${s.stream} · ${s.entity_id}`)}
        ${o("Lamport T (reloj lógico: orden causal)",s.lamport_t)}
        ${o("Causal Taint (quién/por qué escribió)",s.cortex_taint,"mono")}
        ${o("Source (origen del dato)",`${s.source_db??"—"} › ${s.source_table??"—"} › ${s.source_pk??"—"}`,"mono")}
        ${o("Created At",s.created_at,"mono")}
        ${o("Prev Hash (sello del evento anterior)",s.prev_hash,"mono hash")}
        ${o("Entry Hash (SHA3-256 de todo el sobre)",s.entry_hash,"mono hash")}
        <div class="detail-field">
          <div class="detail-field-label">Payload (contenido del evento)</div>
          <pre class="detail-payload">${d(i)}</pre>
        </div>
      </div>
    `,(l=t.querySelector("#detail-close"))==null||l.addEventListener("click",F)}catch(s){const i=t.querySelector(".detail-body");i&&(i.innerHTML=`<span style="color:var(--break)">${d(s.message)}</span>`)}}}function F(){const e=document.getElementById("entry-detail-panel");e&&(e.classList.remove("open"),e.setAttribute("aria-hidden","true"))}async function Je(){const e=document.getElementById("btn-verify-chain"),t=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),l=document.getElementById("verify-progress-bar"),s=document.getElementById("stat-integrity"),i=document.getElementById("verify-summary");if(!t)return;e&&(e.disabled=!0,e.textContent="⚙ Verifying..."),a&&(a.style.display="block"),f("working");let o=0;const c=setInterval(()=>{o=Math.min(o+8,90),l&&(l.style.width=`${o}%`)},120);try{const r=await Le("/api/ledger/verify",{});n.lastVerify=r,clearInterval(c),l&&(l.style.width="100%");const m=r.total_entries??0,u=r.verified_entries??0,y=m-u;t.innerHTML="",(r.entries||[]).slice(0,400).forEach(g=>{const $=document.createElement("div");$.className=`chain-block ${g.valid?"":"invalid"}`,$.title=`Seq ${g.seq} · L:${g.lamport_t} · ${g.valid?"VALID":g.errors.join(" · ")}`,$.addEventListener("click",()=>ee(g.seq)),t.appendChild($)}),m===0&&(t.innerHTML='<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>');const h=r.broken_at!=null;if(s&&(s.textContent=r.valid?"VERIFIED":h?`BROKEN (${y})`:"ERROR",s.className=`stat-value ${r.valid?"verify":"break"}`),i&&(i.textContent=r.valid?`${u}/${m} entries · cadena SHA3-256 intacta`:h?`rota en seq ${r.broken_at} · ${u}/${m} válidas`:r.error||"verificación fallida"),!r.valid&&r.error&&m===0&&(t.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(r.error)}</div>`),r.valid){if(f("done"),E().rewards){const g=document.getElementById("main-content");g==null||g.classList.add("reward-active"),setTimeout(()=>g==null?void 0:g.classList.remove("reward-active"),1400)}}else f("alert"),Y({icon:"⚠",message:h?`Violación de integridad en seq ${r.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`:`Verificación fallida: ${r.error||"error desconocido"}.`,actions:h?[{label:"Inspeccionar entrada",primary:!0,fn:()=>{I(),ee(r.broken_at)}},{label:"Cerrar",fn:I}]:[{label:"Cerrar",primary:!0,fn:I}]});setTimeout(()=>f("idle"),3e3)}catch(r){clearInterval(c),t.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${d(r.message)}</div>`,f("idle")}e&&(e.disabled=!1,e.textContent="⚿ Verify Chain"),a&&setTimeout(()=>{a.style.display="none"},1500)}async function Xe(e){D("databases"),T({breadcrumb:k("BABYLON·60","Ontologies")}),e.innerHTML=`
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
  `;try{const t=await w("/api/databases");n.databaseList=t,Q();const a=document.getElementById("db-table-body"),l=document.getElementById("db-total-count"),s=document.getElementById("db-total-size");if(l&&(l.textContent=t.length),s){const o=t.reduce((c,r)=>c+(r.size_bytes||0),0);s.textContent=o>1e6?`${(o/1e6).toFixed(1)} MB`:`${(o/1024).toFixed(0)} KB`}const i=o=>o.includes("ledger")?"LEDGER":o.includes("ontology")?"ONTOLOGY":o.includes("memory")||o.includes("cortex")?"CORTEX":o.includes("telemetry")?"TELEMETRY":o.includes("nexus")?"NEXUS":"GENERAL";a&&(a.innerHTML=t.map(o=>`
      <tr style="cursor:pointer" data-db="${d(o.name)}" title="Browse tables">
        <td class="stream-cell">${d(o.name)}</td>
        <td class="time-cell">${d(o.size_human||"—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${i(o.name)}</span></td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-db]").forEach(o=>{o.addEventListener("click",()=>Ze(o.dataset.db))})}catch(t){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${d(t.message)}</td></tr>`)}}async function Ze(e){const t=document.getElementById("db-tables-panel"),a=document.getElementById("db-tables-title"),l=document.getElementById("db-tables-body"),s=document.getElementById("db-browse-panel");if(!(!t||!l)){t.style.display="block",s&&(s.style.display="none"),a&&(a.textContent=`Tables — ${e}`),l.innerHTML='<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>',T({breadcrumb:k("BABYLON·60","Ontologies",e)});try{const i=await w(`/api/databases/${encodeURIComponent(e)}/tables`);if(i.length===0){l.innerHTML='<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>';return}l.innerHTML=i.map(o=>`
      <button class="btn" data-table="${d(o.name)}" style="font-size:0.62rem">
        ${d(o.name)} <span style="color:var(--gold);margin-left:4px">${o.row_count}</span>
      </button>
    `).join(""),l.querySelectorAll("[data-table]").forEach(o=>{o.addEventListener("click",()=>et(e,o.dataset.table))})}catch(i){l.innerHTML=`<span style="color:var(--break);font-size:0.68rem">${d(i.message)}</span>`}}}async function et(e,t){const a=document.getElementById("db-browse-panel"),l=document.getElementById("db-browse-title"),s=document.getElementById("db-browse-meta"),i=document.getElementById("db-schema-body"),o=document.getElementById("db-rows-body");if(!(!a||!o)){a.style.display="block",l&&(l.textContent=`${e} › ${t}`),i&&(i.textContent="Loading schema..."),o.innerHTML="",T({breadcrumb:k("BABYLON·60","Ontologies",e,t)});try{const[c,r]=await Promise.all([w(`/api/databases/${encodeURIComponent(e)}/schema/${encodeURIComponent(t)}`),w(`/api/databases/${encodeURIComponent(e)}/tables/${encodeURIComponent(t)}?limit=25`)]);i&&(i.innerHTML=c.map(m=>`<span style="margin-right:12px;white-space:nowrap">${m.pk?"⚿":"·"} ${d(m.name)} <span style="color:var(--dust-ghost)">${d(m.type||"")}</span></span>`).join("")),s&&(s.textContent=`${r.total} rows total · showing ${r.rows.length}`),r.rows.length===0?o.innerHTML='<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>':o.innerHTML=`
        <table class="data-table">
          <thead><tr>${r.columns.map(m=>`<th>${d(m)}</th>`).join("")}</tr></thead>
          <tbody>${r.rows.map(m=>`
            <tr>${r.columns.map(u=>{let y=m[u];y==null&&(y="—"),y=String(y);const h=y.length>90?y.slice(0,90)+"…":y;return`<td title="${d(y.slice(0,400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(h)}</td>`}).join("")}</tr>
          `).join("")}</tbody>
        </table>
      `}catch(c){o.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(c.message)}</div>`}}}async function tt(e){var a,l,s;D("query"),T({breadcrumb:k("BABYLON·60","SQL Console")}),n.databaseList.length===0&&await ke(),e.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${n.databaseList.map(i=>`<option value="${d(i.name)}">${d(i.name)}</option>`).join("")}
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
  `;const t=async()=>{var u,y,h;const i=(y=(u=document.getElementById("query-input"))==null?void 0:u.value)==null?void 0:y.trim(),o=(h=document.getElementById("query-db-select"))==null?void 0:h.value;if(!i||!o)return;f("working");const c=document.getElementById("query-result-card"),r=document.getElementById("query-result-body"),m=document.getElementById("query-result-meta");c&&(c.style.display="block"),r&&(r.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const g=await Le("/api/query",{database:o,sql:i}),$=g.rows||[],H=g.columns||[];m&&(m.textContent=`${g.row_count??$.length} rows · ${g.elapsed_ms??"—"}ms · ${g.database}`),r&&($.length===0?r.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':r.innerHTML=`
            <table class="data-table">
              <thead><tr>${H.map(A=>`<th>${d(A)}</th>`).join("")}</tr></thead>
              <tbody>${$.map(A=>`<tr>${H.map(j=>{let x=A[j];x==null&&(x=""),x=String(x);const N=x.length>120?x.slice(0,120)+"…":x;return`<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d(x.slice(0,400))}">${d(N)}</td>`}).join("")}</tr>`).join("")}</tbody>
            </table>
          `),f("done"),setTimeout(()=>f("idle"),2e3)}catch(g){r&&(r.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${d(g.message)}</div>`),f("idle")}};(a=document.getElementById("btn-run-query"))==null||a.addEventListener("click",t),(l=document.getElementById("btn-clear-query"))==null||l.addEventListener("click",()=>{const i=document.getElementById("query-input");i&&(i.value="");const o=document.getElementById("query-result-card");o&&(o.style.display="none")}),(s=document.getElementById("query-input"))==null||s.addEventListener("keydown",i=>{i.shiftKey&&i.key==="Enter"&&(i.preventDefault(),t())})}async function at(e){if(D("swarm"),T({breadcrumb:k("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'}),e.innerHTML=`
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
  `,nt(),n.telemetrySocket)try{n.telemetrySocket.close()}catch{}f("indexing"),n.telemetrySocket=Ae("/ws/telemetry",t=>{n.telemetrySnapshot=t,st(t),n.tachometerState==="indexing"&&f("idle")},()=>{n.tachometerState==="indexing"&&f("idle")})}function nt(){var s;const e=document.getElementById("swarm-agents");if(!e)return;const t=n.lastVerify,a=n.sentinel,l=[{name:"MOSKV-1 APEX",status:"idle",task:"Meta-orquestador · esperando directiva",progress:0},{name:"BFT Verifier",status:t?t.valid?"done":"error":"idle",task:t?t.valid?`Cadena verificada: ${t.verified_entries}/${t.total_entries}`:`ROTA en seq ${t.broken_at}`:"Sin verificación en esta sesión",progress:t?100:0},{name:"Git Sentinel",status:a?(s=a.warnings)!=null&&s.some(i=>i.level==="red")?"error":"done":"idle",task:a?`${a.repo_name}@${a.branch??"—"} · ${a.dirty_files} dirty · delegación 100% al agente`:"Sin datos de repo",progress:a?100:0},{name:"Telemetry Stream",status:"running",task:"Empujando snapshots del sistema vía WS",progress:100}];e.innerHTML=l.map(i=>`
    <div class="agent-card">
      <div class="agent-card-header">
        <span class="agent-name">${i.name}</span>
        <span class="agent-status-pill ${i.status}">${i.status.toUpperCase()}</span>
      </div>
      <div class="agent-task">${d(i.task)}</div>
      <div class="agent-progress">
        <div class="agent-progress-fill ${i.status==="done"?"done":""}" style="width:${i.progress}%"></div>
      </div>
    </div>
  `).join("")}function st(e){var m,u,y,h;const t=document.getElementById("swarm-log-body");if(!t)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),l=((m=e.databases)==null?void 0:m.length)??0,s=e.total_db_size_mb!=null?`${e.total_db_size_mb}MB`:"—",i=((u=e.wal_files)==null?void 0:u.length)??0,o=((y=e.process)==null?void 0:y.max_rss_mb)!=null?`${e.process.max_rss_mb}MB`:"—",c=(h=e.git)!=null&&h.head?e.git.head.replace("ref: refs/heads/","@"):"",r=document.createElement("div");for(r.className="swarm-log-line",r.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${l} DBs · ${s} · WAL×${i} · RSS ${o} ${c?"· "+d(c):""}</span>
  `,t.appendChild(r);t.children.length>200;)t.removeChild(t.firstChild);t.scrollTop=t.scrollHeight,n.swarmLog.push({time:a,snap:e}),n.swarmLog.length>200&&n.swarmLog.shift()}async function it(e){var o,c,r;D("sentinel"),T({breadcrumb:k("BABYLON·60","Git Sentinel"),actions:'<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>'}),e.innerHTML='<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>';try{n.sentinel=await w("/api/sentinel/status")}catch(m){e.innerHTML=`<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${d(m.message)}</div></div>`;return}se(),P();const t=n.sentinel,a=t.warnings.filter(m=>m.level==="red");t.warnings.filter(m=>m.level==="amber");const l=a.length===0,s=t.warnings.length===0?'<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>':t.warnings.map(m=>`
        <div class="sentinel-warning ${m.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${d(m.msg)}</span>
        </div>
      `).join(""),i=t.remotes.length===0?'<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>':t.remotes.map(m=>`<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${d(m.name)} → ${d(m.url)}</div>`).join("");e.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card" style="border-left:2px solid ${l?"var(--verify)":"var(--break)"}">
        <div class="stat-label">Repo Actual (recalcado siempre — abajo en la barra de estado también)</div>
        <div class="stat-value ${l?"verify":"break"}" style="font-size:1rem">${d(t.repo_name)}</div>
        <div class="stat-sub">@${d(t.branch??"—")} · HEAD ${d(t.head??"—")} · ${t.commit_count??"—"} commits</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Working Tree (árbol de trabajo: cambios sin commitear)</div>
        <div class="stat-value gold">${t.dirty_files}</div>
        <div class="stat-sub">${t.dirty_files===0?"Limpio — todo sellado en git":"ficheros sucios pendientes de commit"}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Último Commit</div>
        <div class="stat-value lapis" style="font-size:0.78rem">${d((t.head_subject||"—").slice(0,44))}</div>
        <div class="stat-sub">${d(String(t.head_time||"—").slice(0,19))}</div>
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Lineage Guard (intuición de repo incorrecto)</div>
      ${s}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--edge-soft)">
        <div style="font-size:0.6rem;color:var(--dust-ghost);margin-bottom:4px">CANON: ${d(t.canonical.repo_name)} @ ${d(t.canonical.branch)} · remotos: ${d(t.canonical.remote_policy)}</div>
        ${i}
      </div>
    </div>

    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:6px">Delegación 100% al Agente</div>
      <div style="font-size:0.66rem;color:var(--dust-dim);margin-bottom:10px">
        Toda mutación hacia la nube (commits, merges, pushes, pre-commits, ships, deploys) se delega a MOSKV-1.
        Tú declaras la intención; el agente ejecuta con Git Sentinel y lo sella en el ledger.
        <span style="color:var(--gold)">Push/deploy bloqueados por P0 (claves expuestas en el fork remoto) hasta rotación.</span>
      </div>
      <div style="display:flex;gap:8px;margin-bottom:10px">
        <input class="input" id="delegation-input" placeholder="Directiva git… ej: 'commit: feat(ide) sentinel + dual mode' o 'push cuando P0 esté resuelto'" style="flex:1">
        <button class="btn btn-primary" id="delegation-add">⚡ Delegar</button>
      </div>
      <div id="delegation-list"></div>
    </div>
  `,(o=document.getElementById("btn-sentinel-refresh"))==null||o.addEventListener("click",()=>Se()),(c=document.getElementById("delegation-add"))==null||c.addEventListener("click",$e),(r=document.getElementById("delegation-input"))==null||r.addEventListener("keydown",m=>{m.key==="Enter"&&$e()}),le()}function $e(){const e=document.getElementById("delegation-input");!e||!e.value.trim()||(n.delegationQueue.unshift({id:Date.now(),text:e.value.trim(),state:"QUEUED",time:new Date().toISOString().slice(0,19)}),n.delegationQueue.length>30&&n.delegationQueue.pop(),localStorage.setItem("b60-delegation",JSON.stringify(n.delegationQueue)),e.value="",le(),E().rewards&&(f("done"),setTimeout(()=>f("idle"),1500)))}function le(){const e=document.getElementById("delegation-list");if(e){if(n.delegationQueue.length===0){e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>';return}e.innerHTML=n.delegationQueue.map(t=>`
    <div class="delegation-item">
      <span class="delegation-state">${t.state}</span>
      <span class="delegation-text">${d(t.text)}</span>
      <span class="delegation-time">${t.time.replace("T"," ")}</span>
      <span class="delegation-del" data-del="${t.id}" title="Retirar directiva">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",()=>{n.delegationQueue=n.delegationQueue.filter(a=>a.id!==parseInt(t.dataset.del)),localStorage.setItem("b60-delegation",JSON.stringify(n.delegationQueue)),le()})})}}
