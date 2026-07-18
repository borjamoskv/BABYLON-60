(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))o(s);new MutationObserver(s=>{for(const i of s)if(i.type==="childList")for(const l of i.addedNodes)l.tagName==="LINK"&&l.rel==="modulepreload"&&o(l)}).observe(document,{childList:!0,subtree:!0});function a(s){const i={};return s.integrity&&(i.integrity=s.integrity),s.referrerPolicy&&(i.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?i.credentials="include":s.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function o(s){if(s.ep)return;s.ep=!0;const i=a(s);fetch(s.href,i)}})();const Le="";async function $(e){const t=await fetch(`${Le}${e}`);if(!t.ok){const a=await t.json().catch(()=>({detail:t.statusText}));throw new Error(a.detail||t.statusText)}return t.json()}async function we(e,t){const a=await fetch(`${Le}${e}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok){const o=await a.json().catch(()=>({detail:a.statusText}));throw new Error(o.detail||a.statusText)}return a.json()}function ke(e,t,a){const o=location.protocol==="https:"?"wss:":"ws:",s={closed:!1,ws:null},i=()=>{if(s.closed)return;const l=new WebSocket(`${o}//${location.host}${e}`);s.ws=l,l.onmessage=m=>{let d;try{d=JSON.parse(m.data)}catch{return}t(d)},l.onerror=m=>a==null?void 0:a(m),l.onclose=()=>{s.closed||setTimeout(i,3e3)}};return s.close=()=>{var l;s.closed=!0;try{(l=s.ws)==null||l.close()}catch{}},i(),s}const O={};let z=null;function C(e,t){O[e]=t}function E(e){if(z===e)return;z=e,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===e)});const t=document.getElementById("main-content");O[e]&&(t.innerHTML="",O[e](t)),history.replaceState(null,"",`#${e}`)}function Se(){const e=document.getElementById("main-content");z&&O[z]&&e&&(e.innerHTML="",O[z](e))}function Me(){const e=location.hash.replace("#","");return e&&O[e]?e:"ledger"}const X={"2e":{key:"2e",label:"2E ◐",name:"Doble Excepcionalidad (TDAH + AACC)",tachometer:!0,loopGuard:!0,restoreBanner:!0,rewards:!0,spineLabels:!1},nt:{key:"nt",label:"NT ○",name:"Neurotípico",tachometer:!1,loopGuard:!1,restoreBanner:!1,rewards:!1,spineLabels:!0}};function x(){return X[n.cognitiveMode]||X["2e"]}function Ee(e){try{const t=JSON.parse(e||"[]");return Array.isArray(t)?t:[]}catch{return[]}}const n={cognitiveMode:localStorage.getItem("b60-cogmode")||"2e",contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:Ee(localStorage.getItem("b60-scratch")),delegationQueue:Ee(localStorage.getItem("b60-delegation")),databaseList:[],ledgerStats:null,lastVerify:null,sentinel:null,sentinelModalShown:!1,telemetrySnapshot:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasVB:{x:80,y:40,w:720,h:400},canvasAbort:null};document.addEventListener("DOMContentLoaded",async()=>{Ie(n.cognitiveMode,{silent:!0}),h("indexing"),Be(),Oe(),Ne(),Ve(),Qe(),Ue(),qe(),Ce(),Fe(),await Promise.all([Ae(),Ye(),De()]),ne(),j(),h("done"),x().restoreBanner&&Ge(localStorage.getItem("b60-route")||"ledger"),E(Me()),h("idle")});function Ie(e,{silent:t=!1}={}){n.cognitiveMode=X[e]?e:"2e",localStorage.setItem("b60-cogmode",n.cognitiveMode),document.body.classList.toggle("mode-2e",n.cognitiveMode==="2e"),document.body.classList.toggle("mode-nt",n.cognitiveMode==="nt");const a=document.getElementById("btn-cogmode");a&&(a.textContent=x().label,a.title=`Modo cognitivo: ${x().name} — click o ⌘⇧E para alternar`),t||(Be(),Se(),U({icon:x().key==="2e"?"◐":"○",message:`Modo cognitivo: ${x().name}. ${x().key==="2e"?"Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos.":"Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."}`}),setTimeout(I,3e3))}function te(){Ie(n.cognitiveMode==="2e"?"nt":"2e")}function Ce(){var t;let e=document.getElementById("btn-cogmode");if(!e){const a=(t=document.getElementById("btn-bifocal"))==null?void 0:t.parentElement;if(a){const o=document.createElement("div");o.className="status-segment",o.innerHTML='<button class="status-bifocal" id="btn-cogmode"></button>',a.parentElement.insertBefore(o,a),e=o.querySelector("#btn-cogmode")}}e&&(e.textContent=x().label,e.title=`Modo cognitivo: ${x().name} — click o ⌘⇧E para alternar`,e.addEventListener("click",te))}function h(e){n.tachometerState=e;const t=document.getElementById("tachometer");t&&(t.className=`tachometer ${e!=="idle"?e:""}`);const a=document.getElementById("status-agent-segment");if(a)if(e==="working"||e==="indexing"){a.style.display="flex";const o=document.getElementById("status-agent-text");o&&(o.textContent=e==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}const _e=[{id:"canvas",icon:"⬡",label:"Canvas",tip:"Architecture Canvas — ABSTRAER  ⌘5"},{id:"ledger",icon:"⧉",label:"Ledger",tip:"BFT Ledger — DETERMINAR  ⌘1"},{id:"databases",icon:"⛁",label:"Ontologies",tip:"Ontologies (explorador SQLite)  ⌘2"},{id:"query",icon:"❯_",label:"SQL",tip:"SQL Console (solo lectura)  ⌘3"},{id:"swarm",icon:"⚡",label:"Swarm",tip:"Agent Swarm (telemetría en vivo)  ⌘4"},{id:"sentinel",icon:"⎇",label:"Sentinel",tip:"Git Sentinel (identidad de repo + delegación)  ⌘6"},{id:"arena",icon:"⚔",label:"Arena",tip:"Arena Matrix (Chatbot Arena)  ⌘7"}];function Be(){const e=document.getElementById("spine");if(!e)return;e.innerHTML="";const t=document.createElement("div");t.className="spine-logo",t.title="BABYLON·60 v1.1.0",t.innerHTML='<div class="spine-logo-dot"></div>',e.appendChild(t);const a=x().spineLabels;_e.forEach((o,s)=>{if(s===1){const l=document.createElement("div");l.className="spine-separator",e.appendChild(l)}const i=document.createElement("button");i.className="spine-icon",i.dataset.route=o.id,a||(i.dataset.tooltip=o.tip),i.setAttribute("aria-label",o.tip),i.innerHTML=a?`<span class="spine-glyph">${o.icon}</span><span class="spine-label">${o.label}</span>`:o.icon,i.addEventListener("click",()=>E(o.id)),e.appendChild(i)}),Te(n.activeRoute)}function Te(e){document.querySelectorAll(".spine-icon").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function Oe(){var e;(e=document.getElementById("btn-collapse-ctx"))==null||e.addEventListener("click",ae),j()}function ae(){n.contextPaneOpen=!n.contextPaneOpen;const e=document.getElementById("context-pane"),t=document.getElementById("btn-collapse-ctx");e&&(e.classList.toggle("collapsed",!n.contextPaneOpen),t&&(t.textContent=n.contextPaneOpen?"⟨":"⟩"))}function j(){var o,s,i,l,m;const e=document.getElementById("context-pane-body");if(!e)return;const t=n.databaseList.slice(0,5).map(d=>`
    <div class="ctx-item depth-1" data-goto-db="${r(d.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${r(d.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `).join(""),a=(s=(o=n.sentinel)==null?void 0:o.warnings)!=null&&s.some(d=>d.level==="red")?'<span class="ctx-item-badge break">!</span>':(l=(i=n.sentinel)==null?void 0:i.warnings)!=null&&l.length?'<span class="ctx-item-badge gold">△</span>':'<span class="ctx-item-badge verify">ok</span>';e.innerHTML=`
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
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${((m=n.ledgerStats)==null?void 0:m.entries)??"—"}</span>
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
  `,e.querySelectorAll(".ctx-item[data-route]").forEach(d=>{d.addEventListener("click",()=>E(d.dataset.route))}),e.querySelectorAll(".ctx-item[data-goto-db]").forEach(d=>{d.addEventListener("click",()=>E("databases"))})}function Q(){var a;const e=document.getElementById("ctx-db-count");e&&(e.textContent=n.databaseList.length||"—");const t=document.getElementById("ctx-ledger-count");t&&(t.textContent=((a=n.ledgerStats)==null?void 0:a.entries)??"—")}function He(e){document.querySelectorAll(".ctx-item[data-route]").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function ne(){var l,m,d;const e=document.getElementById("status-conn-dot"),t=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),o=document.getElementById("status-ledger-entries"),s=document.getElementById("status-lamport"),i=n.ledgerStats!==null||n.databaseList.length>0;e&&(e.className=i?"status-dot":"status-dot error"),t&&(t.textContent=i?"CONNECTED":"OFFLINE"),a&&(a.textContent=n.databaseList.length||"—"),o&&(o.textContent=((l=n.ledgerStats)==null?void 0:l.entries)??"—"),s&&(s.textContent=((d=(m=n.ledgerStats)==null?void 0:m.latest)==null?void 0:d.lamport_t)!=null?`L:${n.ledgerStats.latest.lamport_t}`:"—"),se()}function se(){var i,l;let e=document.getElementById("status-repo-segment");if(!e){const m=document.getElementById("status-bar"),d=m==null?void 0:m.querySelector(".status-segment");if(!m||!d)return;e=document.createElement("div"),e.className="status-segment",e.id="status-repo-segment",e.style.cursor="pointer",e.innerHTML='<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>',d.after(e),e.addEventListener("click",()=>E("sentinel"))}const t=document.getElementById("status-repo-text");if(!t)return;const a=n.sentinel;if(!a){t.textContent="—";return}const o=(i=a.warnings)==null?void 0:i.some(m=>m.level==="red"),s=!o&&((l=a.warnings)==null?void 0:l.length)>0;t.textContent=`${a.repo_name}${a.branch?" @"+a.branch:""}${a.head?" · "+a.head:""}${o?" ⚠":s?" △":" ✓"}`,t.style.color=o?"var(--break)":s?"var(--gold)":"var(--verify)",e.title=o?"LINAJE NO CANÓNICO — abre Git Sentinel":s?"Avisos de linaje — abre Git Sentinel":`Linaje canónico verificado (${a.commit_count??"—"} commits)`}async function De(){var e;try{n.sentinel=await $("/api/sentinel/status"),se();const t=((e=n.sentinel.warnings)==null?void 0:e.filter(a=>a.level==="red"))||[];t.length>0&&!n.sentinelModalShown&&(n.sentinelModalShown=!0,U({icon:"⚠",message:`GIT SENTINEL: ${t[0].msg}`,actions:[{label:"Abrir Sentinel",primary:!0,fn:()=>{I(),E("sentinel")}},{label:"Entendido",fn:I}]}))}catch{}}function qe(){var e;(e=document.getElementById("btn-bifocal"))==null||e.addEventListener("click",ie)}function ie(){n.bifocalMode=n.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",n.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",n.bifocalMode==="micro");const e=document.getElementById("btn-bifocal");e&&(e.textContent=n.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),n.bifocalMode==="macro"&&E("canvas")}const F=[{icon:"⬡",label:"Architecture Canvas",desc:"ABSTRAER: ver el sistema completo",shortcut:"⌘5",action:()=>E("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"DETERMINAR: inspector de cadena de hashes",shortcut:"⌘1",action:()=>E("ledger")},{icon:"⛁",label:"Ontologies",desc:"Explorador SQLite (solo lectura)",shortcut:"⌘2",action:()=>E("databases")},{icon:"❯_",label:"SQL Console",desc:"Consultas read-only contra cualquier .db",shortcut:"⌘3",action:()=>E("query")},{icon:"⚡",label:"Agent Swarm",desc:"Telemetría en vivo (push WS, sin polling)",shortcut:"⌘4",action:()=>E("swarm")},{icon:"⎇",label:"Git Sentinel",desc:"Identidad de repo + delegación de mutaciones git",shortcut:"⌘6",action:()=>E("sentinel")},{icon:"⚿",label:"Verify Chain Integrity",desc:"Recomputar SHA3-256 de toda la cadena",shortcut:"",action:()=>{E("ledger"),setTimeout(()=>{var e;return(e=document.getElementById("btn-verify-chain"))==null?void 0:e.click()},400)}},{icon:"◐",label:"Toggle Cognitive Mode",desc:"Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",shortcut:"⌘⇧E",action:te},{icon:"⟨",label:"Toggle Context Pane",desc:"Mostrar / ocultar mapa semántico",shortcut:"⌘B",action:ae},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Alternar vista bifocal",shortcut:"⌘M",action:ie},{icon:"◎",label:"Open Scratchpad",desc:"Volcar un pensamiento sin perder foco",shortcut:"⌘⇧Space",action:()=>D(!0)}];let S=0,B=[...F];function Ne(){const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.addEventListener("click",a=>{a.target===e&&H()}),t.addEventListener("input",()=>Pe(t.value)),t.addEventListener("keydown",je))}function Re(){n.paletteOpen=!0;const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.classList.add("visible"),e.setAttribute("aria-hidden","false"),t.value="",S=0,B=[...F],G(),setTimeout(()=>t.focus(),50))}function H(){n.paletteOpen=!1;const e=document.getElementById("palette-overlay");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true"))}function Pe(e){const t=e.toLowerCase().trim();S=0,B=t?F.filter(a=>a.label.toLowerCase().includes(t)||a.desc.toLowerCase().includes(t)):[...F],G(t)}function ze(e){return e.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}function G(e=""){const t=document.getElementById("palette-results");if(t){if(B.length===0){t.innerHTML=`<div class="palette-empty">No commands match "<strong>${r(e)}</strong>"</div>`;return}t.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${B.map((a,o)=>{const s=e?a.label.replace(new RegExp(`(${ze(e)})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${o===S?"selected":""}" data-index="${o}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${s}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,t.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const o=parseInt(a.dataset.index);B[o]&&(B[o].action(),H())}),a.addEventListener("mouseenter",()=>{S=parseInt(a.dataset.index),t.querySelectorAll(".palette-item").forEach((o,s)=>o.classList.toggle("selected",s===S))})})}}function je(e){var t,a;if(e.key==="Escape"){H();return}e.key==="ArrowDown"&&(e.preventDefault(),S=Math.min(S+1,B.length-1),G(((t=document.getElementById("palette-input"))==null?void 0:t.value)||"")),e.key==="ArrowUp"&&(e.preventDefault(),S=Math.max(S-1,0),G(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),e.key==="Enter"&&(e.preventDefault(),B[S]&&(B[S].action(),H()))}function Ve(){var a,o;const e=document.getElementById("scratchpad-modal"),t=document.getElementById("scratchpad-input");!e||!t||((a=document.getElementById("scratchpad-save"))==null||a.addEventListener("click",xe),(o=document.getElementById("scratchpad-close"))==null||o.addEventListener("click",()=>D(!1)),t.addEventListener("keydown",s=>{s.key==="Enter"&&!s.shiftKey&&(s.preventDefault(),xe()),s.key==="Escape"&&D(!1)}),oe())}function D(e){const t=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");t&&(n.scratchpadOpen=e!==void 0?e:!n.scratchpadOpen,t.classList.toggle("visible",n.scratchpadOpen),t.setAttribute("aria-hidden",String(!n.scratchpadOpen)),n.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}function xe(){const e=document.getElementById("scratchpad-input");if(!e||!e.value.trim())return;const t={id:Date.now(),text:e.value.trim(),time:new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})};n.scratchpadItems.unshift(t),n.scratchpadItems.length>20&&n.scratchpadItems.pop(),localStorage.setItem("b60-scratch",JSON.stringify(n.scratchpadItems)),e.value="",oe(),j(),x().rewards&&(h("done"),setTimeout(()=>h("idle"),2e3))}function oe(){const e=document.getElementById("scratchpad-items");if(e){if(n.scratchpadItems.length===0){e.innerHTML="";return}e.innerHTML=n.scratchpadItems.map(t=>`
    <div class="scratchpad-item" data-id="${t.id}">
      <span class="scratchpad-item-time">${t.time}</span>
      <span class="scratchpad-item-text">${r(t.text)}</span>
      <span class="scratchpad-item-del" data-del="${t.id}" title="Remove">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",a=>{a.stopPropagation();const o=parseInt(t.dataset.del);n.scratchpadItems=n.scratchpadItems.filter(s=>s.id!==o),localStorage.setItem("b60-scratch",JSON.stringify(n.scratchpadItems)),oe(),j()})})}}function U({icon:e="⬡",message:t,actions:a=[]}){const o=document.getElementById("agent-modal"),s=document.getElementById("agent-modal-icon"),i=document.getElementById("agent-modal-msg"),l=document.getElementById("agent-modal-actions");if(!o||!i||!l)return;s&&(s.textContent=e),i.textContent=t;const m=a.length>0?a:[{label:"Got it",fn:I,primary:!0}];l.innerHTML=m.map((d,c)=>`<button class="btn ${d.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${c}">${d.label}</button>`).join(""),l.querySelectorAll("button").forEach(d=>{d.addEventListener("click",()=>{var c,p;return(p=(c=m[parseInt(d.dataset.actionIdx)])==null?void 0:c.fn)==null?void 0:p.call(c)})}),o.classList.add("visible"),o.setAttribute("aria-hidden","false"),x().tachometer&&h("alert")}function I(){const e=document.getElementById("agent-modal");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true")),h("idle")}function Fe(){setInterval(()=>{if(!x().loopGuard||!n.loopDetector.route||n.loopDetector.interventionFired)return;if(Date.now()-n.loopDetector.routeEnteredAt>1500*1e3){n.loopDetector.interventionFired=!0;const t=n.loopDetector.route;U({icon:"⏱",message:`Llevas más de 25 minutos en ${t.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,actions:[{label:"Ver Arquitectura",primary:!0,fn:()=>{I(),E("canvas")}},{label:"Sigo aquí",fn:I},{label:"Volcar idea →",fn:()=>{I(),D(!0)}}]})}},120*1e3)}function Ge(e){var m;const t=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),o=document.getElementById("restore-points"),s=document.getElementById("restore-dismiss");if(!t||!a)return;const l=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas",sentinel:"Git Sentinel"}[e]||e}`,`${n.databaseList.length||"—"} databases available`,((m=n.ledgerStats)==null?void 0:m.entries)!=null?`${n.ledgerStats.entries} ledger entries`:"Ledger loading...",n.sentinel?`repo ${n.sentinel.repo_name}@${n.sentinel.branch??"—"}`:""].filter(Boolean);a.textContent="Session restored · ",o&&(o.innerHTML=l.map(d=>`<span class="restore-point">${r(d)}</span>`).join("")),t.style.display="flex",s==null||s.addEventListener("click",()=>{t.style.display="none"}),setTimeout(()=>{t.style.display="none"},12e3)}function Qe(){const e={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas",6:"sentinel",7:"arena"};window.addEventListener("keydown",t=>{const a=t.metaKey||t.ctrlKey;if(a&&t.key==="k"&&!t.shiftKey){t.preventDefault(),n.paletteOpen?H():Re();return}if(a&&t.shiftKey&&t.code==="Space"){t.preventDefault(),D();return}if(a&&t.shiftKey&&(t.key==="e"||t.key==="E")){t.preventDefault(),te();return}if(a&&t.key==="b"&&!t.shiftKey){t.preventDefault(),ae();return}if(a&&t.key==="m"&&!t.shiftKey){t.preventDefault(),ie();return}if(a&&e[t.key]){t.preventDefault(),E(e[t.key]);return}if(t.key==="Escape"){if(n.paletteOpen){H();return}if(n.scratchpadOpen){D(!1);return}q()}})}function Ue(){C("canvas",Ke),C("ledger",We),C("databases",Xe),C("query",tt),C("swarm",at),C("sentinel",it),C("arena",ot),window.addEventListener("hashchange",()=>{const e=window.location.hash.replace("#","");e&&E(e)})}async function Ae(){try{n.databaseList=await $("/api/databases"),Q()}catch{}}async function Ye(){try{n.ledgerStats=await $("/api/ledger/stats"),Q(),ne()}catch{}}function T({breadcrumb:e="",actions:t=""}={}){const a=document.getElementById("focus-breadcrumb"),o=document.getElementById("focus-actions");a&&(a.innerHTML=e),o&&(o.innerHTML=t)}function A(...e){return e.map((t,a)=>a<e.length-1?`<span class="breadcrumb-item">${t}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${t}</span>`).join("")}function _(e){n.activeRoute=e,localStorage.setItem("b60-route",e),Te(e),He(e),q(),e!=="swarm"&&n.telemetrySocket&&(n.telemetrySocket.close(),n.telemetrySocket=null),n.loopDetector.route!==e&&(n.loopDetector.route=e,n.loopDetector.routeEnteredAt=Date.now(),n.loopDetector.interventionFired=!1)}function r(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Ke(e){var de,re,ce,me,pe,ue,ve;_("canvas"),T({breadcrumb:A("BABYLON·60","Architecture — ABSTRAER (ver el todo antes que la parte)"),actions:'<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>'});try{n.telemetrySnapshot=await $("/api/telemetry/snapshot")}catch{}const t=n.telemetrySnapshot,a=n.databaseList.length,o=((de=n.ledgerStats)==null?void 0:de.entries)??"—",s=(t==null?void 0:t.total_db_size_mb)!=null?`${t.total_db_size_mb}MB`:"—",i=n.sentinel,l=i!=null&&i.is_git?`${i.repo_name}@${i.branch??"—"} · ${i.head??"—"}`:"no git",m=(re=i==null?void 0:i.warnings)!=null&&re.some(g=>g.level==="red")?"err":(ce=i==null?void 0:i.warnings)!=null&&ce.length?"warn":"ok",d=[{id:"frontend",x:140,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:`Vite · modo ${x().key.toUpperCase()}`,status:"ok"},{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"14 endpoints · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger",meta:`${o} entries · SHA3-256 (huella criptográfica)`,status:(me=n.ledgerStats)!=null&&me.exists?"ok":"err",goto:"ledger"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Ontology DBs",meta:`${a} DBs · ${s} · RO`,status:a>0?"ok":"warn",goto:"databases"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:t?"WS push 2s (sin polling)":"offline",status:t?"ok":"warn",goto:"swarm"},{id:"git",x:140,y:240,type:"SENTINEL",name:"Git Sentinel",meta:l,status:m,goto:"sentinel"}],c=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"git",to:"fastapi"}],p={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};e.innerHTML=`
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
  `;const u=document.getElementById("canvas-svg"),b=document.getElementById("canvas-edges"),v=document.getElementById("canvas-nodes");if(!u||!b||!v)return;c.forEach(({from:g,to:y})=>{const w=d.find(K=>K.id===g),P=d.find(K=>K.id===y);if(!w||!P)return;const ge=w.x+90,ye=w.y+35,fe=P.x,be=P.y+35,M=document.createElementNS("http://www.w3.org/2000/svg","path"),he=(ge+fe)/2;M.setAttribute("d",`M${ge},${ye} C${he},${ye} ${he},${be} ${fe},${be}`),M.setAttribute("stroke","var(--edge)"),M.setAttribute("stroke-width","1.5"),M.setAttribute("fill","none"),M.setAttribute("opacity","0.5"),M.setAttribute("marker-end","url(#arrow)"),b.appendChild(M)}),d.forEach(g=>{const y=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");y.setAttribute("x",g.x),y.setAttribute("y",g.y),y.setAttribute("width","195"),y.setAttribute("height","76");const w=document.createElement("div");w.className="canvas-node-card",w.style.position="relative",w.innerHTML=`
      <div class="canvas-node-type">${g.type}</div>
      <div class="canvas-node-name">${g.name}</div>
      <div class="canvas-node-meta">${r(g.meta)}</div>
      <div class="canvas-node-status" style="background:${p[g.status]||p.idle};box-shadow:0 0 5px ${p[g.status]||p.idle}"></div>
    `,g.goto&&w.addEventListener("click",()=>E(g.goto)),y.appendChild(w),v.appendChild(y)});const f=()=>u.setAttribute("viewBox",`${n.canvasVB.x} ${n.canvasVB.y} ${n.canvasVB.w} ${n.canvasVB.h}`),N=()=>{n.canvasVB={x:80,y:40,w:720,h:400},f()};N();const k=g=>{const y=n.canvasVB,w=y.x+y.w/2,P=y.y+y.h/2;y.w=Math.max(200,Math.min(2e3,y.w*g)),y.h=Math.max(110,Math.min(1100,y.h*g)),y.x=w-y.w/2,y.y=P-y.h/2,f()};(pe=document.getElementById("canvas-zoom-in"))==null||pe.addEventListener("click",()=>k(1/1.2)),(ue=document.getElementById("canvas-zoom-out"))==null||ue.addEventListener("click",()=>k(1.2)),(ve=document.getElementById("canvas-fit-btn"))==null||ve.addEventListener("click",N),u.addEventListener("wheel",g=>{g.preventDefault(),k(g.deltaY>0?1.1:1/1.1)},{passive:!1}),n.canvasAbort&&n.canvasAbort.abort(),n.canvasAbort=new AbortController;const V=n.canvasAbort.signal;let L=!1,R=0,Y=0;u.addEventListener("pointerdown",g=>{L=!0,R=g.clientX,Y=g.clientY}),window.addEventListener("pointermove",g=>{if(!L)return;const y=n.canvasVB.w/u.clientWidth;n.canvasVB.x-=(g.clientX-R)*y,n.canvasVB.y-=(g.clientY-Y)*y,R=g.clientX,Y=g.clientY,f()},{signal:V}),window.addEventListener("pointerup",()=>{L=!1},{signal:V})}let Z=1;const W=50;async function We(e){var t,a,o,s,i;_("ledger"),T({breadcrumb:A("BABYLON·60","BFT Ledger — DETERMINAR (verificar hasta el hash)"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),(t=document.getElementById("btn-verify-chain"))==null||t.addEventListener("click",Je),e.innerHTML=`
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
  `;try{const l=await $("/api/ledger/stats");n.ledgerStats=l;const m=document.getElementById("stat-db-name");m&&(m.textContent=l.db_path||"—");const d=document.getElementById("stat-total-entries");d&&(d.textContent=l.entries??0);const c=document.getElementById("stat-latest-lamport");c&&(c.textContent=`Lamport (reloj lógico causal): ${((a=l.latest)==null?void 0:a.lamport_t)??"—"}`);const p=document.getElementById("stat-latest-time");p&&((o=l.latest)!=null&&o.created_at)&&(p.textContent=String(l.latest.created_at).slice(0,19)),ne(),Q()}catch{}await J(1),(s=document.getElementById("btn-ledger-prev"))==null||s.addEventListener("click",()=>J(Z-1)),(i=document.getElementById("btn-ledger-next"))==null||i.addEventListener("click",()=>J(Z+1))}async function J(e){e<1&&(e=1),Z=e;const t=document.getElementById("ledger-table-body");if(t)try{const a=(e-1)*W,o=await $(`/api/ledger/entries?limit=${W}&offset=${a}`),s=o.entries||[],i=o.total??s.length;s.length===0?t.innerHTML='<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>':(t.innerHTML=s.map(p=>`
        <tr data-seq="${p.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${p.seq}</td>
          <td class="stream-cell">${r(p.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${r(p.entity_id)}</td>
          <td>${r(p.event_type)}</td>
          <td style="color:var(--dust-dim)">${p.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${r(p.cortex_taint)}">${r((p.cortex_taint||"—").slice(0,26))}${(p.cortex_taint||"").length>26?"…":""}</td>
          <td class="time-cell">${String(p.created_at||"").slice(0,19)}</td>
          <td class="hash-cell" title="${r(p.entry_hash)}">${(p.entry_hash||"—").slice(0,12)}…</td>
        </tr>
      `).join(""),t.querySelectorAll("tr[data-seq]").forEach(p=>{p.addEventListener("click",()=>ee(parseInt(p.dataset.seq)))}));const l=Math.max(1,Math.ceil(i/W)),m=document.getElementById("ledger-page-info");m&&(m.textContent=`Page ${e} / ${l} · ${i} entries`);const d=document.getElementById("btn-ledger-prev"),c=document.getElementById("btn-ledger-next");d&&(d.disabled=e<=1),c&&(c.disabled=e>=l)}catch(a){t.innerHTML=`<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${r(a.message)}</td></tr>`}}async function ee(e){var a,o;const t=document.getElementById("entry-detail-panel");if(t){t.classList.add("open"),t.setAttribute("aria-hidden","false"),t.innerHTML=`<div class="detail-header"><span class="detail-title">⧉ Entry #${e}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`,(a=t.querySelector("#detail-close"))==null||a.addEventListener("click",q);try{const s=await $(`/api/ledger/entry/${e}`);let i=s.payload_json||"";try{i=JSON.stringify(JSON.parse(s.payload_json),null,2)}catch{}const l=(m,d,c="")=>`
      <div class="detail-field">
        <div class="detail-field-label">${m}</div>
        <div class="detail-field-value ${c}">${r(d??"—")}</div>
      </div>`;t.innerHTML=`
      <div class="detail-header">
        <span class="detail-title">⧉ Entry #${s.seq} · ${r(s.event_type)}</span>
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
          <pre class="detail-payload">${r(i)}</pre>
        </div>
      </div>
    `,(o=t.querySelector("#detail-close"))==null||o.addEventListener("click",q)}catch(s){const i=t.querySelector(".detail-body");i&&(i.innerHTML=`<span style="color:var(--break)">${r(s.message)}</span>`)}}}function q(){const e=document.getElementById("entry-detail-panel");e&&(e.classList.remove("open"),e.setAttribute("aria-hidden","true"))}async function Je(){const e=document.getElementById("btn-verify-chain"),t=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),o=document.getElementById("verify-progress-bar"),s=document.getElementById("stat-integrity"),i=document.getElementById("verify-summary");if(!t)return;e&&(e.disabled=!0,e.textContent="⚙ Verifying..."),a&&(a.style.display="block"),h("working");let l=0;const m=setInterval(()=>{l=Math.min(l+8,90),o&&(o.style.width=`${l}%`)},120);try{const d=await we("/api/ledger/verify",{});n.lastVerify=d,clearInterval(m),o&&(o.style.width="100%");const c=d.total_entries??0,p=d.verified_entries??0,u=c-p;t.innerHTML="",(d.entries||[]).slice(0,400).forEach(v=>{const f=document.createElement("div");f.className=`chain-block ${v.valid?"":"invalid"}`,f.title=`Seq ${v.seq} · L:${v.lamport_t} · ${v.valid?"VALID":v.errors.join(" · ")}`,f.addEventListener("click",()=>ee(v.seq)),t.appendChild(f)}),c===0&&(t.innerHTML='<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>');const b=d.broken_at!=null;if(s&&(s.textContent=d.valid?"VERIFIED":b?`BROKEN (${u})`:"ERROR",s.className=`stat-value ${d.valid?"verify":"break"}`),i&&(i.textContent=d.valid?`${p}/${c} entries · cadena SHA3-256 intacta`:b?`rota en seq ${d.broken_at} · ${p}/${c} válidas`:d.error||"verificación fallida"),!d.valid&&d.error&&c===0&&(t.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${r(d.error)}</div>`),d.valid){if(h("done"),x().rewards){const v=document.getElementById("main-content");v==null||v.classList.add("reward-active"),setTimeout(()=>v==null?void 0:v.classList.remove("reward-active"),1400)}}else h("alert"),U({icon:"⚠",message:b?`Violación de integridad en seq ${d.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`:`Verificación fallida: ${d.error||"error desconocido"}.`,actions:b?[{label:"Inspeccionar entrada",primary:!0,fn:()=>{I(),ee(d.broken_at)}},{label:"Cerrar",fn:I}]:[{label:"Cerrar",primary:!0,fn:I}]});setTimeout(()=>h("idle"),3e3)}catch(d){clearInterval(m),t.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${r(d.message)}</div>`,h("idle")}e&&(e.disabled=!1,e.textContent="⚿ Verify Chain"),a&&setTimeout(()=>{a.style.display="none"},1500)}async function Xe(e){_("databases"),T({breadcrumb:A("BABYLON·60","Ontologies")}),e.innerHTML=`
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
  `;try{const t=await $("/api/databases");n.databaseList=t,Q();const a=document.getElementById("db-table-body"),o=document.getElementById("db-total-count"),s=document.getElementById("db-total-size");if(o&&(o.textContent=t.length),s){const l=t.reduce((m,d)=>m+(d.size_bytes||0),0);s.textContent=l>1e6?`${(l/1e6).toFixed(1)} MB`:`${(l/1024).toFixed(0)} KB`}const i=l=>l.includes("ledger")?"LEDGER":l.includes("ontology")?"ONTOLOGY":l.includes("memory")||l.includes("cortex")?"CORTEX":l.includes("telemetry")?"TELEMETRY":l.includes("nexus")?"NEXUS":"GENERAL";a&&(a.innerHTML=t.map(l=>`
      <tr style="cursor:pointer" data-db="${r(l.name)}" title="Browse tables">
        <td class="stream-cell">${r(l.name)}</td>
        <td class="time-cell">${r(l.size_human||"—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${i(l.name)}</span></td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-db]").forEach(l=>{l.addEventListener("click",()=>Ze(l.dataset.db))})}catch(t){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${r(t.message)}</td></tr>`)}}async function Ze(e){const t=document.getElementById("db-tables-panel"),a=document.getElementById("db-tables-title"),o=document.getElementById("db-tables-body"),s=document.getElementById("db-browse-panel");if(!(!t||!o)){t.style.display="block",s&&(s.style.display="none"),a&&(a.textContent=`Tables — ${e}`),o.innerHTML='<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>',T({breadcrumb:A("BABYLON·60","Ontologies",e)});try{const i=await $(`/api/databases/${encodeURIComponent(e)}/tables`);if(i.length===0){o.innerHTML='<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>';return}o.innerHTML=i.map(l=>`
      <button class="btn" data-table="${r(l.name)}" style="font-size:0.62rem">
        ${r(l.name)} <span style="color:var(--gold);margin-left:4px">${l.row_count}</span>
      </button>
    `).join(""),o.querySelectorAll("[data-table]").forEach(l=>{l.addEventListener("click",()=>et(e,l.dataset.table))})}catch(i){o.innerHTML=`<span style="color:var(--break);font-size:0.68rem">${r(i.message)}</span>`}}}async function et(e,t){const a=document.getElementById("db-browse-panel"),o=document.getElementById("db-browse-title"),s=document.getElementById("db-browse-meta"),i=document.getElementById("db-schema-body"),l=document.getElementById("db-rows-body");if(!(!a||!l)){a.style.display="block",o&&(o.textContent=`${e} › ${t}`),i&&(i.textContent="Loading schema..."),l.innerHTML="",T({breadcrumb:A("BABYLON·60","Ontologies",e,t)});try{const[m,d]=await Promise.all([$(`/api/databases/${encodeURIComponent(e)}/schema/${encodeURIComponent(t)}`),$(`/api/databases/${encodeURIComponent(e)}/tables/${encodeURIComponent(t)}?limit=25`)]);i&&(i.innerHTML=m.map(c=>`<span style="margin-right:12px;white-space:nowrap">${c.pk?"⚿":"·"} ${r(c.name)} <span style="color:var(--dust-ghost)">${r(c.type||"")}</span></span>`).join("")),s&&(s.textContent=`${d.total} rows total · showing ${d.rows.length}`),d.rows.length===0?l.innerHTML='<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>':l.innerHTML=`
        <table class="data-table">
          <thead><tr>${d.columns.map(c=>`<th>${r(c)}</th>`).join("")}</tr></thead>
          <tbody>${d.rows.map(c=>`
            <tr>${d.columns.map(p=>{let u=c[p];u==null&&(u="—"),u=String(u);const b=u.length>90?u.slice(0,90)+"…":u;return`<td title="${r(u.slice(0,400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r(b)}</td>`}).join("")}</tr>
          `).join("")}</tbody>
        </table>
      `}catch(m){l.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${r(m.message)}</div>`}}}async function tt(e){var a,o,s;_("query"),T({breadcrumb:A("BABYLON·60","SQL Console")}),n.databaseList.length===0&&await Ae(),e.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${n.databaseList.map(i=>`<option value="${r(i.name)}">${r(i.name)}</option>`).join("")}
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
  `;const t=async()=>{var p,u,b;const i=(u=(p=document.getElementById("query-input"))==null?void 0:p.value)==null?void 0:u.trim(),l=(b=document.getElementById("query-db-select"))==null?void 0:b.value;if(!i||!l)return;h("working");const m=document.getElementById("query-result-card"),d=document.getElementById("query-result-body"),c=document.getElementById("query-result-meta");m&&(m.style.display="block"),d&&(d.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const v=await we("/api/query",{database:l,sql:i}),f=v.rows||[],N=v.columns||[];c&&(c.textContent=`${v.row_count??f.length} rows · ${v.elapsed_ms??"—"}ms · ${v.database}`),d&&(f.length===0?d.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':d.innerHTML=`
            <table class="data-table">
              <thead><tr>${N.map(k=>`<th>${r(k)}</th>`).join("")}</tr></thead>
              <tbody>${f.map(k=>`<tr>${N.map(V=>{let L=k[V];L==null&&(L=""),L=String(L);const R=L.length>120?L.slice(0,120)+"…":L;return`<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r(L.slice(0,400))}">${r(R)}</td>`}).join("")}</tr>`).join("")}</tbody>
            </table>
          `),h("done"),setTimeout(()=>h("idle"),2e3)}catch(v){d&&(d.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${r(v.message)}</div>`),h("idle")}};(a=document.getElementById("btn-run-query"))==null||a.addEventListener("click",t),(o=document.getElementById("btn-clear-query"))==null||o.addEventListener("click",()=>{const i=document.getElementById("query-input");i&&(i.value="");const l=document.getElementById("query-result-card");l&&(l.style.display="none")}),(s=document.getElementById("query-input"))==null||s.addEventListener("keydown",i=>{i.shiftKey&&i.key==="Enter"&&(i.preventDefault(),t())})}async function at(e){if(_("swarm"),T({breadcrumb:A("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'}),e.innerHTML=`
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
  `,nt(),n.telemetrySocket)try{n.telemetrySocket.close()}catch{}h("indexing"),n.telemetrySocket=ke("/ws/telemetry",t=>{n.telemetrySnapshot=t,st(t),n.tachometerState==="indexing"&&h("idle")},()=>{n.tachometerState==="indexing"&&h("idle")})}function nt(){var s;const e=document.getElementById("swarm-agents");if(!e)return;const t=n.lastVerify,a=n.sentinel,o=[{name:"MOSKV-1 APEX",status:"idle",task:"Meta-orquestador · esperando directiva",progress:0},{name:"BFT Verifier",status:t?t.valid?"done":"error":"idle",task:t?t.valid?`Cadena verificada: ${t.verified_entries}/${t.total_entries}`:`ROTA en seq ${t.broken_at}`:"Sin verificación en esta sesión",progress:t?100:0},{name:"Git Sentinel",status:a?(s=a.warnings)!=null&&s.some(i=>i.level==="red")?"error":"done":"idle",task:a?`${a.repo_name}@${a.branch??"—"} · ${a.dirty_files} dirty · delegación 100% al agente`:"Sin datos de repo",progress:a?100:0},{name:"Telemetry Stream",status:"running",task:"Empujando snapshots del sistema vía WS",progress:100}];e.innerHTML=o.map(i=>`
    <div class="agent-card">
      <div class="agent-card-header">
        <span class="agent-name">${i.name}</span>
        <span class="agent-status-pill ${i.status}">${i.status.toUpperCase()}</span>
      </div>
      <div class="agent-task">${r(i.task)}</div>
      <div class="agent-progress">
        <div class="agent-progress-fill ${i.status==="done"?"done":""}" style="width:${i.progress}%"></div>
      </div>
    </div>
  `).join("")}function st(e){var c,p,u,b;const t=document.getElementById("swarm-log-body");if(!t)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),o=((c=e.databases)==null?void 0:c.length)??0,s=e.total_db_size_mb!=null?`${e.total_db_size_mb}MB`:"—",i=((p=e.wal_files)==null?void 0:p.length)??0,l=((u=e.process)==null?void 0:u.max_rss_mb)!=null?`${e.process.max_rss_mb}MB`:"—",m=(b=e.git)!=null&&b.head?e.git.head.replace("ref: refs/heads/","@"):"",d=document.createElement("div");for(d.className="swarm-log-line",d.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${o} DBs · ${s} · WAL×${i} · RSS ${l} ${m?"· "+r(m):""}</span>
  `,t.appendChild(d);t.children.length>200;)t.removeChild(t.firstChild);t.scrollTop=t.scrollHeight,n.swarmLog.push({time:a,snap:e}),n.swarmLog.length>200&&n.swarmLog.shift()}async function it(e){var l,m,d;_("sentinel"),T({breadcrumb:A("BABYLON·60","Git Sentinel"),actions:'<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>'}),e.innerHTML='<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>';try{n.sentinel=await $("/api/sentinel/status")}catch(c){e.innerHTML=`<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${r(c.message)}</div></div>`;return}se(),j();const t=n.sentinel,a=t.warnings.filter(c=>c.level==="red");t.warnings.filter(c=>c.level==="amber");const o=a.length===0,s=t.warnings.length===0?'<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>':t.warnings.map(c=>`
        <div class="sentinel-warning ${c.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${r(c.msg)}</span>
        </div>
      `).join(""),i=t.remotes.length===0?'<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>':t.remotes.map(c=>`<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${r(c.name)} → ${r(c.url)}</div>`).join("");e.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card" style="border-left:2px solid ${o?"var(--verify)":"var(--break)"}">
        <div class="stat-label">Repo Actual (recalcado siempre — abajo en la barra de estado también)</div>
        <div class="stat-value ${o?"verify":"break"}" style="font-size:1rem">${r(t.repo_name)}</div>
        <div class="stat-sub">@${r(t.branch??"—")} · HEAD ${r(t.head??"—")} · ${t.commit_count??"—"} commits</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Working Tree (árbol de trabajo: cambios sin commitear)</div>
        <div class="stat-value gold">${t.dirty_files}</div>
        <div class="stat-sub">${t.dirty_files===0?"Limpio — todo sellado en git":"ficheros sucios pendientes de commit"}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Último Commit</div>
        <div class="stat-value lapis" style="font-size:0.78rem">${r((t.head_subject||"—").slice(0,44))}</div>
        <div class="stat-sub">${r(String(t.head_time||"—").slice(0,19))}</div>
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Lineage Guard (intuición de repo incorrecto)</div>
      ${s}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--edge-soft)">
        <div style="font-size:0.6rem;color:var(--dust-ghost);margin-bottom:4px">CANON: ${r(t.canonical.repo_name)} @ ${r(t.canonical.branch)} · remotos: ${r(t.canonical.remote_policy)}</div>
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
  `,(l=document.getElementById("btn-sentinel-refresh"))==null||l.addEventListener("click",()=>Se()),(m=document.getElementById("delegation-add"))==null||m.addEventListener("click",$e),(d=document.getElementById("delegation-input"))==null||d.addEventListener("keydown",c=>{c.key==="Enter"&&$e()}),le()}function $e(){const e=document.getElementById("delegation-input");!e||!e.value.trim()||(n.delegationQueue.unshift({id:Date.now(),text:e.value.trim(),state:"QUEUED",time:new Date().toISOString().slice(0,19)}),n.delegationQueue.length>30&&n.delegationQueue.pop(),localStorage.setItem("b60-delegation",JSON.stringify(n.delegationQueue)),e.value="",le(),x().rewards&&(h("done"),setTimeout(()=>h("idle"),1500)))}function le(){const e=document.getElementById("delegation-list");if(e){if(n.delegationQueue.length===0){e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>';return}e.innerHTML=n.delegationQueue.map(t=>`
    <div class="delegation-item">
      <span class="delegation-state">${t.state}</span>
      <span class="delegation-text">${r(t.text)}</span>
      <span class="delegation-time">${t.time.replace("T"," ")}</span>
      <span class="delegation-del" data-del="${t.id}" title="Retirar directiva">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",()=>{n.delegationQueue=n.delegationQueue.filter(a=>a.id!==parseInt(t.dataset.del)),localStorage.setItem("b60-delegation",JSON.stringify(n.delegationQueue)),le()})})}}async function ot(e){_("arena"),T({breadcrumb:A("BABYLON·60","Arena Matrix"),actions:'<span class="focus-badge live">ARENA MATRIX</span>'}),e.innerHTML=`
    <div class="arena-layout">
      <!-- LEADERBOARD PANEL -->
      <div class="arena-panel">
        <div class="arena-panel-header">
          <span>⚔ LMSYS Leaderboard Sync</span>
          <div class="arena-meta" id="arena-leaderboard-meta"></div>
        </div>
        <div class="arena-panel-body" style="padding:0;">
          <table class="data-table" id="arena-leaderboard-table">
            <thead>
              <tr>
                <th style="width:50px; text-align:center;">Rank</th>
                <th>Model</th>
                <th>Vendor</th>
                <th>Elo Score</th>
                <th>Votes</th>
                <th style="width:80px;">Exergy</th>
                <th>Risk</th>
              </tr>
            </thead>
            <tbody>
              <tr><td colspan="7" style="text-align:center;color:var(--dust-faint);padding:16px;">Loading leaderboard data...</td></tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- SIDE ACTIONS / DETAILS PANEL -->
      <div style="display:flex; flex-direction:column; gap:16px; overflow:hidden; height:100%;">
        <!-- BATTLES PANEL -->
        <div class="arena-panel" style="flex: 1; overflow:hidden;">
          <div class="arena-panel-header">
            <span>⚡ Domestic battles (DOM)</span>
          </div>
          <div class="arena-panel-body" id="arena-battles-body" style="overflow-y:auto; padding:12px;">
            <div style="color:var(--dust-faint); font-size:0.7rem; text-align:center; padding:16px;">Loading battles...</div>
          </div>
        </div>

        <!-- HF CONVERSATIONS PANEL -->
        <div class="arena-panel" style="flex: 1; overflow:hidden;">
          <div class="arena-panel-header">
            <span>⬡ Dataset: toxic-chat (Hugging Face)</span>
          </div>
          <div class="arena-panel-body" id="arena-toxic-body" style="overflow-y:auto; padding:12px;">
            <div style="color:var(--dust-faint); font-size:0.7rem; text-align:center; padding:16px;">Loading conversations...</div>
          </div>
        </div>
      </div>
    </div>
  `;try{const[t,a,o]=await Promise.all([$("/api/arena/leaderboard").catch(()=>({exists:!1,models:[]})),$("/api/arena/battles").catch(()=>({exists:!1,battles:[]})),$("/api/arena/conversations").catch(()=>({exists:!1,conversations:[]}))]),s=document.querySelector("#arena-leaderboard-table tbody"),i=document.getElementById("arena-leaderboard-meta");if(t.exists&&t.models.length>0){const d=t.meta;i.innerHTML=`
        <span>Latency: <b>${d.latency_ms}ms</b></span>
        <span>Entropy: <b>${d.entropy?d.entropy.toFixed(4):"—"}</b></span>
        <span>Updated: <b>${d.fetched_at?d.fetched_at.slice(11,19):"Recent"}</b></span>
      `,s.innerHTML=t.models.map(c=>{let p="rating-C",u="C",b="",v="Unknown";const f=c.model.toLowerCase();return f.includes("claude")||f.includes("qwen")||f.includes("llama")?(u="A",p="rating-A"):(f.includes("gemini")||f.includes("gpt"))&&(u="B",p="rating-B"),f.includes("claude")?(v="Moderate-High (RLHF)",b="risk-moderate"):f.includes("gpt")||f.includes("gemini")?(v="High (Strict refusal)",b="risk-high"):(f.includes("llama")||f.includes("qwen"))&&(v="Low-Moderate",b=""),`
          <tr>
            <td class="seq-cell" style="text-align:center;">#${c.rank}</td>
            <td class="stream-cell">${r(c.model)}</td>
            <td>${r(c.vendor)}</td>
            <td><b>${c.score}</b></td>
            <td>${c.votes}</td>
            <td><span class="exergy-badge ${p}">${u}</span></td>
            <td><span class="risk-tag ${b}">${v}</span></td>
          </tr>
        `}).join("")}else s.innerHTML='<tr><td colspan="7" style="text-align:center;color:var(--break);padding:16px;">No leaderboard data found in ojeador_leaderboard.db.</td></tr>';const l=document.getElementById("arena-battles-body");a.exists&&a.battles.length>0?(l.innerHTML=a.battles.map(d=>`
        <div class="battle-item" data-id="${d.id}">
          <div class="battle-header">
            <span>Vector: <b>${r(d.vector)}</b></span>
            <span class="battle-winner">WINNER: ${r(d.winner)}</span>
          </div>
          <div style="font-weight:700; color:var(--dust-dim); margin-bottom:4px;">${r(d.model_a)} vs ${r(d.model_b)}</div>
          <div class="chat-bubble">${r(d.prompt)}</div>
        </div>
      `).join(""),l.querySelectorAll(".battle-item").forEach(d=>{d.addEventListener("click",()=>{const c=parseInt(d.dataset.id),p=a.battles.find(u=>u.id===c);p&&lt(p)})})):l.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem;text-align:center;padding:24px;">No domestic battles recorded yet. Start arena_automata.py to run battles.</div>';const m=document.getElementById("arena-toxic-body");o.exists&&o.conversations.length>0?(m.innerHTML=`
        <div class="toxic-list">
          ${o.conversations.map((d,c)=>{const p=d.toxicity.toLowerCase()!=="none / none",u=p?"toxic-pill":"toxic-pill safe",b=p?"TOXIC/Jailbreak":"SAFE";return`
              <div class="toxic-item" data-idx="${c}">
                <div class="toxic-meta">
                  <span>ID: <b>${d.conv_id.slice(0,12)}...</b></span>
                  <span class="${u}">${b}</span>
                </div>
                <div class="chat-bubble">${r(d.prompt)}</div>
              </div>
            `}).join("")}
        </div>
      `,m.querySelectorAll(".toxic-item").forEach(d=>{d.addEventListener("click",()=>{const c=parseInt(d.dataset.idx),p=o.conversations[c];p&&dt(p)})})):m.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem;text-align:center;padding:24px;">Dataset conversations sample not found or empty.</div>'}catch(t){console.error(t)}}function lt(e){var o;const t=document.getElementById("entry-detail-panel");if(!t)return;t.classList.add("open"),t.setAttribute("aria-hidden","false");const a=(s,i,l="")=>`
    <div class="detail-field">
      <div class="detail-field-label">${s}</div>
      <div class="detail-field-value ${l}">${r(i??"—")}</div>
    </div>`;t.innerHTML=`
    <div class="detail-header">
      <span class="detail-title">⚡ Battle #${e.id} detail</span>
      <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button>
    </div>
    <div class="detail-body">
      ${a("Timestamp",e.timestamp,"mono")}
      ${a("Vector Category",e.vector)}
      ${a("Model A",e.model_a,"stream-cell")}
      ${a("Model B",e.model_b,"stream-cell")}
      ${a("Winner",e.winner,"battle-winner")}
      ${a("Cortex Taint Hash",e.cortex_taint_hash,"mono hash")}
      ${a("Entropy A / B",`${e.entropy_a?e.entropy_a.toFixed(4):"—"} / ${e.entropy_b?e.entropy_b.toFixed(4):"—"}`)}
      
      <div class="detail-field">
        <div class="detail-field-label">Battle Prompt</div>
        <pre class="detail-payload" style="max-height:120px; overflow-y:auto;">${r(e.prompt)}</pre>
      </div>

      <div class="detail-field">
        <div class="detail-field-label">Response A (${r(e.model_a)})</div>
        <pre class="detail-payload" style="max-height:160px; overflow-y:auto;">${r(e.response_a)}</pre>
      </div>

      <div class="detail-field">
        <div class="detail-field-label">Response B (${r(e.model_b)})</div>
        <pre class="detail-payload" style="max-height:160px; overflow-y:auto;">${r(e.response_b)}</pre>
      </div>
    </div>
  `,(o=t.querySelector("#detail-close"))==null||o.addEventListener("click",q)}function dt(e){var o;const t=document.getElementById("entry-detail-panel");if(!t)return;t.classList.add("open"),t.setAttribute("aria-hidden","false");const a=(s,i,l="")=>`
    <div class="detail-field">
      <div class="detail-field-label">${s}</div>
      <div class="detail-field-value ${l}">${r(i??"—")}</div>
    </div>`;t.innerHTML=`
    <div class="detail-header">
      <span class="detail-title">⬡ Conversation Detail</span>
      <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button>
    </div>
    <div class="detail-body">
      ${a("HF Conversation ID",e.conv_id,"mono")}
      ${a("Toxicity / Jailbreak Class",e.toxicity,"mono")}
      
      <div class="detail-field">
        <div class="detail-field-label">User Input (Prompt)</div>
        <pre class="detail-payload" style="max-height:180px; overflow-y:auto;">${r(e.prompt)}</pre>
      </div>

      <div class="detail-field">
        <div class="detail-field-label">Model Output (Response)</div>
        <pre class="detail-payload" style="max-height:280px; overflow-y:auto;">${r(e.response)}</pre>
      </div>
    </div>
  `,(o=t.querySelector("#detail-close"))==null||o.addEventListener("click",q)}
