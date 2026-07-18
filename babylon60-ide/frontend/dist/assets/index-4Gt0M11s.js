(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const n of document.querySelectorAll('link[rel="modulepreload"]'))l(n);new MutationObserver(n=>{for(const i of n)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&l(o)}).observe(document,{childList:!0,subtree:!0});function a(n){const i={};return n.integrity&&(i.integrity=n.integrity),n.referrerPolicy&&(i.referrerPolicy=n.referrerPolicy),n.crossOrigin==="use-credentials"?i.credentials="include":n.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function l(n){if(n.ep)return;n.ep=!0;const i=a(n);fetch(n.href,i)}})();const Le="";async function w(e){const t=await fetch(`${Le}${e}`);if(!t.ok){const a=await t.json().catch(()=>({detail:t.statusText}));throw new Error(a.detail||t.statusText)}return t.json()}async function G(e,t){const a=await fetch(`${Le}${e}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok){const l=await a.json().catch(()=>({detail:a.statusText}));throw new Error(l.detail||a.statusText)}return a.json()}function ke(e,t,a){const l=location.protocol==="https:"?"wss:":"ws:",n={closed:!1,ws:null},i=()=>{if(n.closed)return;const o=new WebSocket(`${l}//${location.host}${e}`);n.ws=o,o.onmessage=c=>{let r;try{r=JSON.parse(c.data)}catch{return}t(r)},o.onerror=c=>a==null?void 0:a(c),o.onclose=()=>{n.closed||setTimeout(i,3e3)}};return n.close=()=>{var o;n.closed=!0;try{(o=n.ws)==null||o.close()}catch{}},i(),n}const N={};let j=null;function C(e,t){N[e]=t}function $(e){if(j===e)return;j=e,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===e)});const t=document.getElementById("main-content");N[e]&&(t.innerHTML="",N[e](t)),history.replaceState(null,"",`#${e}`)}function Ie(){const e=document.getElementById("main-content");j&&N[j]&&e&&(e.innerHTML="",N[j](e))}function Me(){const e=location.hash.replace("#","");return e&&N[e]?e:"ledger"}const Z={"2e":{key:"2e",label:"2E ◐",name:"Doble Excepcionalidad (TDAH + AACC)",tachometer:!0,loopGuard:!0,restoreBanner:!0,rewards:!0,spineLabels:!1},nt:{key:"nt",label:"NT ○",name:"Neurotípico",tachometer:!1,loopGuard:!1,restoreBanner:!1,rewards:!1,spineLabels:!0}};function L(){return Z[s.cognitiveMode]||Z["2e"]}function Ee(e){try{const t=JSON.parse(e||"[]");return Array.isArray(t)?t:[]}catch{return[]}}const s={cognitiveMode:localStorage.getItem("b60-cogmode")||"2e",contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:Ee(localStorage.getItem("b60-scratch")),delegationQueue:Ee(localStorage.getItem("b60-delegation")),databaseList:[],ledgerStats:null,lastVerify:null,sentinel:null,sentinelModalShown:!1,telemetrySnapshot:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasVB:{x:80,y:40,w:720,h:400},canvasAbort:null};document.addEventListener("DOMContentLoaded",async()=>{Se(s.cognitiveMode,{silent:!0}),y("indexing"),Be(),Oe(),qe(),Ve(),Qe(),Ue(),Ne(),Ce(),Ge(),await Promise.all([Ae(),Ye(),De()]),se(),V(),y("done"),L().restoreBanner&&Fe(localStorage.getItem("b60-route")||"ledger"),$(Me()),y("idle")});function Se(e,{silent:t=!1}={}){s.cognitiveMode=Z[e]?e:"2e",localStorage.setItem("b60-cogmode",s.cognitiveMode),document.body.classList.toggle("mode-2e",s.cognitiveMode==="2e"),document.body.classList.toggle("mode-nt",s.cognitiveMode==="nt");const a=document.getElementById("btn-cogmode");a&&(a.textContent=L().label,a.title=`Modo cognitivo: ${L().name} — click o ⌘⇧E para alternar`),t||(Be(),Ie(),Y({icon:L().key==="2e"?"◐":"○",message:`Modo cognitivo: ${L().name}. ${L().key==="2e"?"Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos.":"Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."}`}),setTimeout(B,3e3))}function ae(){Se(s.cognitiveMode==="2e"?"nt":"2e")}function Ce(){var t;let e=document.getElementById("btn-cogmode");if(!e){const a=(t=document.getElementById("btn-bifocal"))==null?void 0:t.parentElement;if(a){const l=document.createElement("div");l.className="status-segment",l.innerHTML='<button class="status-bifocal" id="btn-cogmode"></button>',a.parentElement.insertBefore(l,a),e=l.querySelector("#btn-cogmode")}}e&&(e.textContent=L().label,e.title=`Modo cognitivo: ${L().name} — click o ⌘⇧E para alternar`,e.addEventListener("click",ae))}function y(e){s.tachometerState=e;const t=document.getElementById("tachometer");t&&(t.className=`tachometer ${e!=="idle"?e:""}`);const a=document.getElementById("status-agent-segment");if(a)if(e==="working"||e==="indexing"){a.style.display="flex";const l=document.getElementById("status-agent-text");l&&(l.textContent=e==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}const _e=[{id:"canvas",icon:"⬡",label:"Canvas",tip:"Architecture Canvas — ABSTRAER  ⌘5"},{id:"ledger",icon:"⧉",label:"Ledger",tip:"BFT Ledger — DETERMINAR  ⌘1"},{id:"databases",icon:"⛁",label:"Ontologies",tip:"Ontologies (explorador SQLite)  ⌘2"},{id:"query",icon:"❯_",label:"SQL",tip:"SQL Console (solo lectura)  ⌘3"},{id:"swarm",icon:"⚡",label:"Swarm",tip:"Agent Swarm (telemetría en vivo)  ⌘4"},{id:"sentinel",icon:"⎇",label:"Sentinel",tip:"Git Sentinel (identidad de repo + delegación)  ⌘6"},{id:"arena",icon:"⚔",label:"Arena",tip:"Arena Matrix (Chatbot Arena)  ⌘7"},{id:"inference",icon:"◈",label:"Inference",tip:"Local Inference Console — ⌘8"}];function Be(){const e=document.getElementById("spine");if(!e)return;e.innerHTML="";const t=document.createElement("div");t.className="spine-logo",t.title="BABYLON·60 v1.1.0",t.innerHTML='<div class="spine-logo-dot"></div>',e.appendChild(t);const a=L().spineLabels;_e.forEach((l,n)=>{if(n===1){const o=document.createElement("div");o.className="spine-separator",e.appendChild(o)}const i=document.createElement("button");i.className="spine-icon",i.dataset.route=l.id,a||(i.dataset.tooltip=l.tip),i.setAttribute("aria-label",l.tip),i.innerHTML=a?`<span class="spine-glyph">${l.icon}</span><span class="spine-label">${l.label}</span>`:l.icon,i.addEventListener("click",()=>$(l.id)),e.appendChild(i)}),Te(s.activeRoute)}function Te(e){document.querySelectorAll(".spine-icon").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function Oe(){var e;(e=document.getElementById("btn-collapse-ctx"))==null||e.addEventListener("click",ne),V()}function ne(){s.contextPaneOpen=!s.contextPaneOpen;const e=document.getElementById("context-pane"),t=document.getElementById("btn-collapse-ctx");e&&(e.classList.toggle("collapsed",!s.contextPaneOpen),t&&(t.textContent=s.contextPaneOpen?"⟨":"⟩"))}function V(){var l,n,i,o,c;const e=document.getElementById("context-pane-body");if(!e)return;const t=s.databaseList.slice(0,5).map(r=>`
    <div class="ctx-item depth-1" data-goto-db="${d(r.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${d(r.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `).join(""),a=(n=(l=s.sentinel)==null?void 0:l.warnings)!=null&&n.some(r=>r.level==="red")?'<span class="ctx-item-badge break">!</span>':(o=(i=s.sentinel)==null?void 0:i.warnings)!=null&&o.length?'<span class="ctx-item-badge gold">△</span>':'<span class="ctx-item-badge verify">ok</span>';e.innerHTML=`
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
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${((c=s.ledgerStats)==null?void 0:c.entries)??"—"}</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">${s.databaseList.length||"—"}</span>
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
        ${s.scratchpadItems.length===0?'<span style="color:var(--dust-ghost)">No notes yet</span>':`<span style="color:var(--dust-dim)">${s.scratchpadItems.length} note${s.scratchpadItems.length>1?"s":""}</span>`}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Databases</div>
      ${t||'<div style="padding:4px 12px;font-size:0.62rem;color:var(--dust-ghost)">No .db discovered</div>'}
    </div>
  `,e.querySelectorAll(".ctx-item[data-route]").forEach(r=>{r.addEventListener("click",()=>$(r.dataset.route))}),e.querySelectorAll(".ctx-item[data-goto-db]").forEach(r=>{r.addEventListener("click",()=>$("databases"))})}function U(){var a;const e=document.getElementById("ctx-db-count");e&&(e.textContent=s.databaseList.length||"—");const t=document.getElementById("ctx-ledger-count");t&&(t.textContent=((a=s.ledgerStats)==null?void 0:a.entries)??"—")}function He(e){document.querySelectorAll(".ctx-item[data-route]").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function se(){var o,c,r;const e=document.getElementById("status-conn-dot"),t=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),l=document.getElementById("status-ledger-entries"),n=document.getElementById("status-lamport"),i=s.ledgerStats!==null||s.databaseList.length>0;e&&(e.className=i?"status-dot":"status-dot error"),t&&(t.textContent=i?"CONNECTED":"OFFLINE"),a&&(a.textContent=s.databaseList.length||"—"),l&&(l.textContent=((o=s.ledgerStats)==null?void 0:o.entries)??"—"),n&&(n.textContent=((r=(c=s.ledgerStats)==null?void 0:c.latest)==null?void 0:r.lamport_t)!=null?`L:${s.ledgerStats.latest.lamport_t}`:"—"),ie()}function ie(){var i,o;let e=document.getElementById("status-repo-segment");if(!e){const c=document.getElementById("status-bar"),r=c==null?void 0:c.querySelector(".status-segment");if(!c||!r)return;e=document.createElement("div"),e.className="status-segment",e.id="status-repo-segment",e.style.cursor="pointer",e.innerHTML='<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>',r.after(e),e.addEventListener("click",()=>$("sentinel"))}const t=document.getElementById("status-repo-text");if(!t)return;const a=s.sentinel;if(!a){t.textContent="—";return}const l=(i=a.warnings)==null?void 0:i.some(c=>c.level==="red"),n=!l&&((o=a.warnings)==null?void 0:o.length)>0;t.textContent=`${a.repo_name}${a.branch?" @"+a.branch:""}${a.head?" · "+a.head:""}${l?" ⚠":n?" △":" ✓"}`,t.style.color=l?"var(--break)":n?"var(--gold)":"var(--verify)",e.title=l?"LINAJE NO CANÓNICO — abre Git Sentinel":n?"Avisos de linaje — abre Git Sentinel":`Linaje canónico verificado (${a.commit_count??"—"} commits)`}async function De(){var e;try{s.sentinel=await w("/api/sentinel/status"),ie();const t=((e=s.sentinel.warnings)==null?void 0:e.filter(a=>a.level==="red"))||[];t.length>0&&!s.sentinelModalShown&&(s.sentinelModalShown=!0,Y({icon:"⚠",message:`GIT SENTINEL: ${t[0].msg}`,actions:[{label:"Abrir Sentinel",primary:!0,fn:()=>{B(),$("sentinel")}},{label:"Entendido",fn:B}]}))}catch{}}function Ne(){var e;(e=document.getElementById("btn-bifocal"))==null||e.addEventListener("click",oe)}function oe(){s.bifocalMode=s.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",s.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",s.bifocalMode==="micro");const e=document.getElementById("btn-bifocal");e&&(e.textContent=s.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),s.bifocalMode==="macro"&&$("canvas")}const F=[{icon:"⬡",label:"Architecture Canvas",desc:"ABSTRAER: ver el sistema completo",shortcut:"⌘5",action:()=>$("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"DETERMINAR: inspector de cadena de hashes",shortcut:"⌘1",action:()=>$("ledger")},{icon:"⛁",label:"Ontologies",desc:"Explorador SQLite (solo lectura)",shortcut:"⌘2",action:()=>$("databases")},{icon:"❯_",label:"SQL Console",desc:"Consultas read-only contra cualquier .db",shortcut:"⌘3",action:()=>$("query")},{icon:"⚡",label:"Agent Swarm",desc:"Telemetría en vivo (push WS, sin polling)",shortcut:"⌘4",action:()=>$("swarm")},{icon:"⎇",label:"Git Sentinel",desc:"Identidad de repo + delegación de mutaciones git",shortcut:"⌘6",action:()=>$("sentinel")},{icon:"⚿",label:"Verify Chain Integrity",desc:"Recomputar SHA3-256 de toda la cadena",shortcut:"",action:()=>{$("ledger"),setTimeout(()=>{var e;return(e=document.getElementById("btn-verify-chain"))==null?void 0:e.click()},400)}},{icon:"◐",label:"Toggle Cognitive Mode",desc:"Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",shortcut:"⌘⇧E",action:ae},{icon:"⟨",label:"Toggle Context Pane",desc:"Mostrar / ocultar mapa semántico",shortcut:"⌘B",action:ne},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Alternar vista bifocal",shortcut:"⌘M",action:oe},{icon:"◎",label:"Open Scratchpad",desc:"Volcar un pensamiento sin perder foco",shortcut:"⌘⇧Space",action:()=>R(!0)}];let S=0,k=[...F];function qe(){const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.addEventListener("click",a=>{a.target===e&&q()}),t.addEventListener("input",()=>ze(t.value)),t.addEventListener("keydown",je))}function Re(){s.paletteOpen=!0;const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.classList.add("visible"),e.setAttribute("aria-hidden","false"),t.value="",S=0,k=[...F],Q(),setTimeout(()=>t.focus(),50))}function q(){s.paletteOpen=!1;const e=document.getElementById("palette-overlay");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true"))}function ze(e){const t=e.toLowerCase().trim();S=0,k=t?F.filter(a=>a.label.toLowerCase().includes(t)||a.desc.toLowerCase().includes(t)):[...F],Q(t)}function Pe(e){return e.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}function Q(e=""){const t=document.getElementById("palette-results");if(t){if(k.length===0){t.innerHTML=`<div class="palette-empty">No commands match "<strong>${d(e)}</strong>"</div>`;return}t.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${k.map((a,l)=>{const n=e?a.label.replace(new RegExp(`(${Pe(e)})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${l===S?"selected":""}" data-index="${l}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${n}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,t.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const l=parseInt(a.dataset.index);k[l]&&(k[l].action(),q())}),a.addEventListener("mouseenter",()=>{S=parseInt(a.dataset.index),t.querySelectorAll(".palette-item").forEach((l,n)=>l.classList.toggle("selected",n===S))})})}}function je(e){var t,a;if(e.key==="Escape"){q();return}e.key==="ArrowDown"&&(e.preventDefault(),S=Math.min(S+1,k.length-1),Q(((t=document.getElementById("palette-input"))==null?void 0:t.value)||"")),e.key==="ArrowUp"&&(e.preventDefault(),S=Math.max(S-1,0),Q(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),e.key==="Enter"&&(e.preventDefault(),k[S]&&(k[S].action(),q()))}function Ve(){var a,l;const e=document.getElementById("scratchpad-modal"),t=document.getElementById("scratchpad-input");!e||!t||((a=document.getElementById("scratchpad-save"))==null||a.addEventListener("click",$e),(l=document.getElementById("scratchpad-close"))==null||l.addEventListener("click",()=>R(!1)),t.addEventListener("keydown",n=>{n.key==="Enter"&&!n.shiftKey&&(n.preventDefault(),$e()),n.key==="Escape"&&R(!1)}),le())}function R(e){const t=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");t&&(s.scratchpadOpen=e!==void 0?e:!s.scratchpadOpen,t.classList.toggle("visible",s.scratchpadOpen),t.setAttribute("aria-hidden",String(!s.scratchpadOpen)),s.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}function $e(){const e=document.getElementById("scratchpad-input");if(!e||!e.value.trim())return;const t={id:Date.now(),text:e.value.trim(),time:new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})};s.scratchpadItems.unshift(t),s.scratchpadItems.length>20&&s.scratchpadItems.pop(),localStorage.setItem("b60-scratch",JSON.stringify(s.scratchpadItems)),e.value="",le(),V(),L().rewards&&(y("done"),setTimeout(()=>y("idle"),2e3))}function le(){const e=document.getElementById("scratchpad-items");if(e){if(s.scratchpadItems.length===0){e.innerHTML="";return}e.innerHTML=s.scratchpadItems.map(t=>`
    <div class="scratchpad-item" data-id="${t.id}">
      <span class="scratchpad-item-time">${t.time}</span>
      <span class="scratchpad-item-text">${d(t.text)}</span>
      <span class="scratchpad-item-del" data-del="${t.id}" title="Remove">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",a=>{a.stopPropagation();const l=parseInt(t.dataset.del);s.scratchpadItems=s.scratchpadItems.filter(n=>n.id!==l),localStorage.setItem("b60-scratch",JSON.stringify(s.scratchpadItems)),le(),V()})})}}function Y({icon:e="⬡",message:t,actions:a=[]}){const l=document.getElementById("agent-modal"),n=document.getElementById("agent-modal-icon"),i=document.getElementById("agent-modal-msg"),o=document.getElementById("agent-modal-actions");if(!l||!i||!o)return;n&&(n.textContent=e),i.textContent=t;const c=a.length>0?a:[{label:"Got it",fn:B,primary:!0}];o.innerHTML=c.map((r,u)=>`<button class="btn ${r.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${u}">${r.label}</button>`).join(""),o.querySelectorAll("button").forEach(r=>{r.addEventListener("click",()=>{var u,p;return(p=(u=c[parseInt(r.dataset.actionIdx)])==null?void 0:u.fn)==null?void 0:p.call(u)})}),l.classList.add("visible"),l.setAttribute("aria-hidden","false"),L().tachometer&&y("alert")}function B(){const e=document.getElementById("agent-modal");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true")),y("idle")}function Ge(){setInterval(()=>{if(!L().loopGuard||!s.loopDetector.route||s.loopDetector.interventionFired)return;if(Date.now()-s.loopDetector.routeEnteredAt>1500*1e3){s.loopDetector.interventionFired=!0;const t=s.loopDetector.route;Y({icon:"⏱",message:`Llevas más de 25 minutos en ${t.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,actions:[{label:"Ver Arquitectura",primary:!0,fn:()=>{B(),$("canvas")}},{label:"Sigo aquí",fn:B},{label:"Volcar idea →",fn:()=>{B(),R(!0)}}]})}},120*1e3)}function Fe(e){var c;const t=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),l=document.getElementById("restore-points"),n=document.getElementById("restore-dismiss");if(!t||!a)return;const o=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas",sentinel:"Git Sentinel"}[e]||e}`,`${s.databaseList.length||"—"} databases available`,((c=s.ledgerStats)==null?void 0:c.entries)!=null?`${s.ledgerStats.entries} ledger entries`:"Ledger loading...",s.sentinel?`repo ${s.sentinel.repo_name}@${s.sentinel.branch??"—"}`:""].filter(Boolean);a.textContent="Session restored · ",l&&(l.innerHTML=o.map(r=>`<span class="restore-point">${d(r)}</span>`).join("")),t.style.display="flex",n==null||n.addEventListener("click",()=>{t.style.display="none"}),setTimeout(()=>{t.style.display="none"},12e3)}function Qe(){const e={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas",6:"sentinel",7:"arena",8:"inference"};window.addEventListener("keydown",t=>{const a=t.metaKey||t.ctrlKey;if(a&&t.key==="k"&&!t.shiftKey){t.preventDefault(),s.paletteOpen?q():Re();return}if(a&&t.shiftKey&&t.code==="Space"){t.preventDefault(),R();return}if(a&&t.shiftKey&&(t.key==="e"||t.key==="E")){t.preventDefault(),ae();return}if(a&&t.key==="b"&&!t.shiftKey){t.preventDefault(),ne();return}if(a&&t.key==="m"&&!t.shiftKey){t.preventDefault(),oe();return}if(a&&e[t.key]){t.preventDefault(),$(e[t.key]);return}if(t.key==="Escape"){if(s.paletteOpen){q();return}if(s.scratchpadOpen){R(!1);return}z()}})}function Ue(){C("canvas",Ke),C("ledger",We),C("databases",Xe),C("query",tt),C("swarm",at),C("sentinel",it),C("arena",ot),C("inference",dt),window.addEventListener("hashchange",()=>{const e=window.location.hash.replace("#","");e&&$(e)})}async function Ae(){try{s.databaseList=await w("/api/databases"),U()}catch{}}async function Ye(){try{s.ledgerStats=await w("/api/ledger/stats"),U(),se()}catch{}}function T({breadcrumb:e="",actions:t=""}={}){const a=document.getElementById("focus-breadcrumb"),l=document.getElementById("focus-actions");a&&(a.innerHTML=e),l&&(l.innerHTML=t)}function A(...e){return e.map((t,a)=>a<e.length-1?`<span class="breadcrumb-item">${t}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${t}</span>`).join("")}function _(e){s.activeRoute=e,localStorage.setItem("b60-route",e),Te(e),He(e),z(),e!=="swarm"&&s.telemetrySocket&&(s.telemetrySocket.close(),s.telemetrySocket=null),s.loopDetector.route!==e&&(s.loopDetector.route=e,s.loopDetector.routeEnteredAt=Date.now(),s.loopDetector.interventionFired=!1)}function d(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Ke(e){var de,ce,pe,me,ue,ve,ge;_("canvas"),T({breadcrumb:A("BABYLON·60","Architecture — ABSTRAER (ver el todo antes que la parte)"),actions:'<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>'});try{s.telemetrySnapshot=await w("/api/telemetry/snapshot")}catch{}const t=s.telemetrySnapshot,a=s.databaseList.length,l=((de=s.ledgerStats)==null?void 0:de.entries)??"—",n=(t==null?void 0:t.total_db_size_mb)!=null?`${t.total_db_size_mb}MB`:"—",i=s.sentinel,o=i!=null&&i.is_git?`${i.repo_name}@${i.branch??"—"} · ${i.head??"—"}`:"no git",c=(ce=i==null?void 0:i.warnings)!=null&&ce.some(g=>g.level==="red")?"err":(pe=i==null?void 0:i.warnings)!=null&&pe.length?"warn":"ok",r=[{id:"frontend",x:140,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:`Vite · modo ${L().key.toUpperCase()}`,status:"ok"},{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"14 endpoints · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger",meta:`${l} entries · SHA3-256 (huella criptográfica)`,status:(me=s.ledgerStats)!=null&&me.exists?"ok":"err",goto:"ledger"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Ontology DBs",meta:`${a} DBs · ${n} · RO`,status:a>0?"ok":"warn",goto:"databases"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:t?"WS push 2s (sin polling)":"offline",status:t?"ok":"warn",goto:"swarm"},{id:"git",x:140,y:240,type:"SENTINEL",name:"Git Sentinel",meta:o,status:c,goto:"sentinel"}],u=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"git",to:"fastapi"}],p={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};e.innerHTML=`
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
  `;const m=document.getElementById("canvas-svg"),b=document.getElementById("canvas-edges"),v=document.getElementById("canvas-nodes");if(!m||!b||!v)return;u.forEach(({from:g,to:h})=>{const I=r.find(W=>W.id===g),P=r.find(W=>W.id===h);if(!I||!P)return;const fe=I.x+90,ye=I.y+35,be=P.x,he=P.y+35,H=document.createElementNS("http://www.w3.org/2000/svg","path"),xe=(fe+be)/2;H.setAttribute("d",`M${fe},${ye} C${xe},${ye} ${xe},${he} ${be},${he}`),H.setAttribute("stroke","var(--edge)"),H.setAttribute("stroke-width","1.5"),H.setAttribute("fill","none"),H.setAttribute("opacity","0.5"),H.setAttribute("marker-end","url(#arrow)"),b.appendChild(H)}),r.forEach(g=>{const h=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");h.setAttribute("x",g.x),h.setAttribute("y",g.y),h.setAttribute("width","195"),h.setAttribute("height","76");const I=document.createElement("div");I.className="canvas-node-card",I.style.position="relative",I.innerHTML=`
      <div class="canvas-node-type">${g.type}</div>
      <div class="canvas-node-name">${g.name}</div>
      <div class="canvas-node-meta">${d(g.meta)}</div>
      <div class="canvas-node-status" style="background:${p[g.status]||p.idle};box-shadow:0 0 5px ${p[g.status]||p.idle}"></div>
    `,g.goto&&I.addEventListener("click",()=>$(g.goto)),h.appendChild(I),v.appendChild(h)});const f=()=>m.setAttribute("viewBox",`${s.canvasVB.x} ${s.canvasVB.y} ${s.canvasVB.w} ${s.canvasVB.h}`),M=()=>{s.canvasVB={x:80,y:40,w:720,h:400},f()};M();const E=g=>{const h=s.canvasVB,I=h.x+h.w/2,P=h.y+h.h/2;h.w=Math.max(200,Math.min(2e3,h.w*g)),h.h=Math.max(110,Math.min(1100,h.h*g)),h.x=I-h.w/2,h.y=P-h.h/2,f()};(ue=document.getElementById("canvas-zoom-in"))==null||ue.addEventListener("click",()=>E(1/1.2)),(ve=document.getElementById("canvas-zoom-out"))==null||ve.addEventListener("click",()=>E(1.2)),(ge=document.getElementById("canvas-fit-btn"))==null||ge.addEventListener("click",M),m.addEventListener("wheel",g=>{g.preventDefault(),E(g.deltaY>0?1.1:1/1.1)},{passive:!1}),s.canvasAbort&&s.canvasAbort.abort(),s.canvasAbort=new AbortController;const D=s.canvasAbort.signal;let x=!1,O=0,K=0;m.addEventListener("pointerdown",g=>{x=!0,O=g.clientX,K=g.clientY}),window.addEventListener("pointermove",g=>{if(!x)return;const h=s.canvasVB.w/m.clientWidth;s.canvasVB.x-=(g.clientX-O)*h,s.canvasVB.y-=(g.clientY-K)*h,O=g.clientX,K=g.clientY,f()},{signal:D}),window.addEventListener("pointerup",()=>{x=!1},{signal:D})}let ee=1;const J=50;async function We(e){var t,a,l,n,i;_("ledger"),T({breadcrumb:A("BABYLON·60","BFT Ledger — DETERMINAR (verificar hasta el hash)"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),(t=document.getElementById("btn-verify-chain"))==null||t.addEventListener("click",Je),e.innerHTML=`
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
  `;try{const o=await w("/api/ledger/stats");s.ledgerStats=o;const c=document.getElementById("stat-db-name");c&&(c.textContent=o.db_path||"—");const r=document.getElementById("stat-total-entries");r&&(r.textContent=o.entries??0);const u=document.getElementById("stat-latest-lamport");u&&(u.textContent=`Lamport (reloj lógico causal): ${((a=o.latest)==null?void 0:a.lamport_t)??"—"}`);const p=document.getElementById("stat-latest-time");p&&((l=o.latest)!=null&&l.created_at)&&(p.textContent=String(o.latest.created_at).slice(0,19)),se(),U()}catch{}await X(1),(n=document.getElementById("btn-ledger-prev"))==null||n.addEventListener("click",()=>X(ee-1)),(i=document.getElementById("btn-ledger-next"))==null||i.addEventListener("click",()=>X(ee+1))}async function X(e){e<1&&(e=1),ee=e;const t=document.getElementById("ledger-table-body");if(t)try{const a=(e-1)*J,l=await w(`/api/ledger/entries?limit=${J}&offset=${a}`),n=l.entries||[],i=l.total??n.length;n.length===0?t.innerHTML='<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>':(t.innerHTML=n.map(p=>`
        <tr data-seq="${p.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${p.seq}</td>
          <td class="stream-cell">${d(p.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${d(p.entity_id)}</td>
          <td>${d(p.event_type)}</td>
          <td style="color:var(--dust-dim)">${p.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${d(p.cortex_taint)}">${d((p.cortex_taint||"—").slice(0,26))}${(p.cortex_taint||"").length>26?"…":""}</td>
          <td class="time-cell">${String(p.created_at||"").slice(0,19)}</td>
          <td class="hash-cell" title="${d(p.entry_hash)}">${(p.entry_hash||"—").slice(0,12)}…</td>
        </tr>
      `).join(""),t.querySelectorAll("tr[data-seq]").forEach(p=>{p.addEventListener("click",()=>te(parseInt(p.dataset.seq)))}));const o=Math.max(1,Math.ceil(i/J)),c=document.getElementById("ledger-page-info");c&&(c.textContent=`Page ${e} / ${o} · ${i} entries`);const r=document.getElementById("btn-ledger-prev"),u=document.getElementById("btn-ledger-next");r&&(r.disabled=e<=1),u&&(u.disabled=e>=o)}catch(a){t.innerHTML=`<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${d(a.message)}</td></tr>`}}async function te(e){var a,l;const t=document.getElementById("entry-detail-panel");if(t){t.classList.add("open"),t.setAttribute("aria-hidden","false"),t.innerHTML=`<div class="detail-header"><span class="detail-title">⧉ Entry #${e}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`,(a=t.querySelector("#detail-close"))==null||a.addEventListener("click",z);try{const n=await w(`/api/ledger/entry/${e}`);let i=n.payload_json||"";try{i=JSON.stringify(JSON.parse(n.payload_json),null,2)}catch{}const o=(c,r,u="")=>`
      <div class="detail-field">
        <div class="detail-field-label">${c}</div>
        <div class="detail-field-value ${u}">${d(r??"—")}</div>
      </div>`;t.innerHTML=`
      <div class="detail-header">
        <span class="detail-title">⧉ Entry #${n.seq} · ${d(n.event_type)}</span>
        <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button>
      </div>
      <div class="detail-body">
        ${o("Event ID (UUID v5: determinista, mismo input → mismo id)",n.event_id,"mono")}
        ${o("Stream · Entity",`${n.stream} · ${n.entity_id}`)}
        ${o("Lamport T (reloj lógico: orden causal)",n.lamport_t)}
        ${o("Causal Taint (quién/por qué escribió)",n.cortex_taint,"mono")}
        ${o("Source (origen del dato)",`${n.source_db??"—"} › ${n.source_table??"—"} › ${n.source_pk??"—"}`,"mono")}
        ${o("Created At",n.created_at,"mono")}
        ${o("Prev Hash (sello del evento anterior)",n.prev_hash,"mono hash")}
        ${o("Entry Hash (SHA3-256 de todo el sobre)",n.entry_hash,"mono hash")}
        <div class="detail-field">
          <div class="detail-field-label">Payload (contenido del evento)</div>
          <pre class="detail-payload">${d(i)}</pre>
        </div>
      </div>
    `,(l=t.querySelector("#detail-close"))==null||l.addEventListener("click",z)}catch(n){const i=t.querySelector(".detail-body");i&&(i.innerHTML=`<span style="color:var(--break)">${d(n.message)}</span>`)}}}function z(){const e=document.getElementById("entry-detail-panel");e&&(e.classList.remove("open"),e.setAttribute("aria-hidden","true"))}async function Je(){const e=document.getElementById("btn-verify-chain"),t=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),l=document.getElementById("verify-progress-bar"),n=document.getElementById("stat-integrity"),i=document.getElementById("verify-summary");if(!t)return;e&&(e.disabled=!0,e.textContent="⚙ Verifying..."),a&&(a.style.display="block"),y("working");let o=0;const c=setInterval(()=>{o=Math.min(o+8,90),l&&(l.style.width=`${o}%`)},120);try{const r=await G("/api/ledger/verify",{});s.lastVerify=r,clearInterval(c),l&&(l.style.width="100%");const u=r.total_entries??0,p=r.verified_entries??0,m=u-p;t.innerHTML="",(r.entries||[]).slice(0,400).forEach(v=>{const f=document.createElement("div");f.className=`chain-block ${v.valid?"":"invalid"}`,f.title=`Seq ${v.seq} · L:${v.lamport_t} · ${v.valid?"VALID":v.errors.join(" · ")}`,f.addEventListener("click",()=>te(v.seq)),t.appendChild(f)}),u===0&&(t.innerHTML='<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>');const b=r.broken_at!=null;if(n&&(n.textContent=r.valid?"VERIFIED":b?`BROKEN (${m})`:"ERROR",n.className=`stat-value ${r.valid?"verify":"break"}`),i&&(i.textContent=r.valid?`${p}/${u} entries · cadena SHA3-256 intacta`:b?`rota en seq ${r.broken_at} · ${p}/${u} válidas`:r.error||"verificación fallida"),!r.valid&&r.error&&u===0&&(t.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(r.error)}</div>`),r.valid){if(y("done"),L().rewards){const v=document.getElementById("main-content");v==null||v.classList.add("reward-active"),setTimeout(()=>v==null?void 0:v.classList.remove("reward-active"),1400)}}else y("alert"),Y({icon:"⚠",message:b?`Violación de integridad en seq ${r.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`:`Verificación fallida: ${r.error||"error desconocido"}.`,actions:b?[{label:"Inspeccionar entrada",primary:!0,fn:()=>{B(),te(r.broken_at)}},{label:"Cerrar",fn:B}]:[{label:"Cerrar",primary:!0,fn:B}]});setTimeout(()=>y("idle"),3e3)}catch(r){clearInterval(c),t.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${d(r.message)}</div>`,y("idle")}e&&(e.disabled=!1,e.textContent="⚿ Verify Chain"),a&&setTimeout(()=>{a.style.display="none"},1500)}async function Xe(e){_("databases"),T({breadcrumb:A("BABYLON·60","Ontologies")}),e.innerHTML=`
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
  `;try{const t=await w("/api/databases");s.databaseList=t,U();const a=document.getElementById("db-table-body"),l=document.getElementById("db-total-count"),n=document.getElementById("db-total-size");if(l&&(l.textContent=t.length),n){const o=t.reduce((c,r)=>c+(r.size_bytes||0),0);n.textContent=o>1e6?`${(o/1e6).toFixed(1)} MB`:`${(o/1024).toFixed(0)} KB`}const i=o=>o.includes("ledger")?"LEDGER":o.includes("ontology")?"ONTOLOGY":o.includes("memory")||o.includes("cortex")?"CORTEX":o.includes("telemetry")?"TELEMETRY":o.includes("nexus")?"NEXUS":"GENERAL";a&&(a.innerHTML=t.map(o=>`
      <tr style="cursor:pointer" data-db="${d(o.name)}" title="Browse tables">
        <td class="stream-cell">${d(o.name)}</td>
        <td class="time-cell">${d(o.size_human||"—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${i(o.name)}</span></td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-db]").forEach(o=>{o.addEventListener("click",()=>Ze(o.dataset.db))})}catch(t){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${d(t.message)}</td></tr>`)}}async function Ze(e){const t=document.getElementById("db-tables-panel"),a=document.getElementById("db-tables-title"),l=document.getElementById("db-tables-body"),n=document.getElementById("db-browse-panel");if(!(!t||!l)){t.style.display="block",n&&(n.style.display="none"),a&&(a.textContent=`Tables — ${e}`),l.innerHTML='<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>',T({breadcrumb:A("BABYLON·60","Ontologies",e)});try{const i=await w(`/api/databases/${encodeURIComponent(e)}/tables`);if(i.length===0){l.innerHTML='<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>';return}l.innerHTML=i.map(o=>`
      <button class="btn" data-table="${d(o.name)}" style="font-size:0.62rem">
        ${d(o.name)} <span style="color:var(--gold);margin-left:4px">${o.row_count}</span>
      </button>
    `).join(""),l.querySelectorAll("[data-table]").forEach(o=>{o.addEventListener("click",()=>et(e,o.dataset.table))})}catch(i){l.innerHTML=`<span style="color:var(--break);font-size:0.68rem">${d(i.message)}</span>`}}}async function et(e,t){const a=document.getElementById("db-browse-panel"),l=document.getElementById("db-browse-title"),n=document.getElementById("db-browse-meta"),i=document.getElementById("db-schema-body"),o=document.getElementById("db-rows-body");if(!(!a||!o)){a.style.display="block",l&&(l.textContent=`${e} › ${t}`),i&&(i.textContent="Loading schema..."),o.innerHTML="",T({breadcrumb:A("BABYLON·60","Ontologies",e,t)});try{const[c,r]=await Promise.all([w(`/api/databases/${encodeURIComponent(e)}/schema/${encodeURIComponent(t)}`),w(`/api/databases/${encodeURIComponent(e)}/tables/${encodeURIComponent(t)}?limit=25`)]);i&&(i.innerHTML=c.map(u=>`<span style="margin-right:12px;white-space:nowrap">${u.pk?"⚿":"·"} ${d(u.name)} <span style="color:var(--dust-ghost)">${d(u.type||"")}</span></span>`).join("")),n&&(n.textContent=`${r.total} rows total · showing ${r.rows.length}`),r.rows.length===0?o.innerHTML='<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>':o.innerHTML=`
        <table class="data-table">
          <thead><tr>${r.columns.map(u=>`<th>${d(u)}</th>`).join("")}</tr></thead>
          <tbody>${r.rows.map(u=>`
            <tr>${r.columns.map(p=>{let m=u[p];m==null&&(m="—"),m=String(m);const b=m.length>90?m.slice(0,90)+"…":m;return`<td title="${d(m.slice(0,400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(b)}</td>`}).join("")}</tr>
          `).join("")}</tbody>
        </table>
      `}catch(c){o.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(c.message)}</div>`}}}async function tt(e){var a,l,n;_("query"),T({breadcrumb:A("BABYLON·60","SQL Console")}),s.databaseList.length===0&&await Ae(),e.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${s.databaseList.map(i=>`<option value="${d(i.name)}">${d(i.name)}</option>`).join("")}
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
  `;const t=async()=>{var p,m,b;const i=(m=(p=document.getElementById("query-input"))==null?void 0:p.value)==null?void 0:m.trim(),o=(b=document.getElementById("query-db-select"))==null?void 0:b.value;if(!i||!o)return;y("working");const c=document.getElementById("query-result-card"),r=document.getElementById("query-result-body"),u=document.getElementById("query-result-meta");c&&(c.style.display="block"),r&&(r.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const v=await G("/api/query",{database:o,sql:i}),f=v.rows||[],M=v.columns||[];u&&(u.textContent=`${v.row_count??f.length} rows · ${v.elapsed_ms??"—"}ms · ${v.database}`),r&&(f.length===0?r.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':r.innerHTML=`
            <table class="data-table">
              <thead><tr>${M.map(E=>`<th>${d(E)}</th>`).join("")}</tr></thead>
              <tbody>${f.map(E=>`<tr>${M.map(D=>{let x=E[D];x==null&&(x=""),x=String(x);const O=x.length>120?x.slice(0,120)+"…":x;return`<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d(x.slice(0,400))}">${d(O)}</td>`}).join("")}</tr>`).join("")}</tbody>
            </table>
          `),y("done"),setTimeout(()=>y("idle"),2e3)}catch(v){r&&(r.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${d(v.message)}</div>`),y("idle")}};(a=document.getElementById("btn-run-query"))==null||a.addEventListener("click",t),(l=document.getElementById("btn-clear-query"))==null||l.addEventListener("click",()=>{const i=document.getElementById("query-input");i&&(i.value="");const o=document.getElementById("query-result-card");o&&(o.style.display="none")}),(n=document.getElementById("query-input"))==null||n.addEventListener("keydown",i=>{i.shiftKey&&i.key==="Enter"&&(i.preventDefault(),t())})}async function at(e){if(_("swarm"),T({breadcrumb:A("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'}),e.innerHTML=`
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
  `,nt(),s.telemetrySocket)try{s.telemetrySocket.close()}catch{}y("indexing"),s.telemetrySocket=ke("/ws/telemetry",t=>{s.telemetrySnapshot=t,st(t),s.tachometerState==="indexing"&&y("idle")},()=>{s.tachometerState==="indexing"&&y("idle")})}function nt(){var n;const e=document.getElementById("swarm-agents");if(!e)return;const t=s.lastVerify,a=s.sentinel,l=[{name:"MOSKV-1 APEX",status:"idle",task:"Meta-orquestador · esperando directiva",progress:0},{name:"BFT Verifier",status:t?t.valid?"done":"error":"idle",task:t?t.valid?`Cadena verificada: ${t.verified_entries}/${t.total_entries}`:`ROTA en seq ${t.broken_at}`:"Sin verificación en esta sesión",progress:t?100:0},{name:"Git Sentinel",status:a?(n=a.warnings)!=null&&n.some(i=>i.level==="red")?"error":"done":"idle",task:a?`${a.repo_name}@${a.branch??"—"} · ${a.dirty_files} dirty · delegación 100% al agente`:"Sin datos de repo",progress:a?100:0},{name:"Telemetry Stream",status:"running",task:"Empujando snapshots del sistema vía WS",progress:100}];e.innerHTML=l.map(i=>`
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
  `).join("")}function st(e){var u,p,m,b;const t=document.getElementById("swarm-log-body");if(!t)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),l=((u=e.databases)==null?void 0:u.length)??0,n=e.total_db_size_mb!=null?`${e.total_db_size_mb}MB`:"—",i=((p=e.wal_files)==null?void 0:p.length)??0,o=((m=e.process)==null?void 0:m.max_rss_mb)!=null?`${e.process.max_rss_mb}MB`:"—",c=(b=e.git)!=null&&b.head?e.git.head.replace("ref: refs/heads/","@"):"",r=document.createElement("div");for(r.className="swarm-log-line",r.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${l} DBs · ${n} · WAL×${i} · RSS ${o} ${c?"· "+d(c):""}</span>
  `,t.appendChild(r);t.children.length>200;)t.removeChild(t.firstChild);t.scrollTop=t.scrollHeight,s.swarmLog.push({time:a,snap:e}),s.swarmLog.length>200&&s.swarmLog.shift()}async function it(e){var r,u,p;_("sentinel"),T({breadcrumb:A("BABYLON·60","Git Sentinel"),actions:'<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>'}),e.innerHTML='<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>';let t,a=[];try{t=await w("/api/sentinel/status"),s.sentinel=t}catch(m){e.innerHTML=`<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${d(m.message)}</div></div>`;return}try{a=(await w("/api/sentinel/exergy")).history||[]}catch(m){console.error("No se pudo obtener historial de exergía:",m)}ie(),V();const l=t.warnings.filter(m=>m.level==="red");t.warnings.filter(m=>m.level==="amber");const n=l.length===0,i=t.warnings.length===0?'<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>':t.warnings.map(m=>`
        <div class="sentinel-warning ${m.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${d(m.msg)}</span>
        </div>
      `).join(""),o=t.remotes.length===0?'<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>':t.remotes.map(m=>`<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${d(m.name)} → ${d(m.url)}</div>`).join(""),c=a.length===0?'<div style="color:var(--dust-ghost);font-size:0.64rem">Sin auditorías de exergía registradas en el Ledger.</div>':a.slice(0,10).map(m=>`
        <div class="delegation-item" style="border-left:2px solid ${m.exergy_score>=700?"var(--verify)":"var(--break)"}; padding-left: 8px; margin-bottom: 6px; display: flex; flex-direction: column;">
          <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
            <span style="font-weight:bold; font-size:0.7rem; color:${m.exergy_score>=700?"var(--verify)":"var(--break)"}">${m.exergy_score.toFixed(1)}/1000.0</span>
            <span style="font-family:var(--font-mono); font-size:0.6rem; color:var(--dust-dim)">HEAD: ${d(m.commit_hash.slice(0,8))}</span>
          </div>
          <div style="color:var(--dust-heavy); font-size:0.62rem; line-height: 1.2;">G: ${d(m.gradient)}</div>
          <div style="color:var(--dust-dim); font-size:0.58rem; margin-top: 1px;">E: ${d(m.entropy)}</div>
        </div>
      `).join("");e.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card" style="border-left:2px solid ${n?"var(--verify)":"var(--break)"}">
        <div class="stat-label">Repo Actual (recalcado siempre — abajo en la barra de estado también)</div>
        <div class="stat-value ${n?"verify":"break"}" style="font-size:1rem">${d(t.repo_name)}</div>
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
      ${i}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--edge-soft)">
        <div style="font-size:0.6rem;color:var(--dust-ghost);margin-bottom:4px">CANON: ${d(t.canonical.repo_name)} @ ${d(t.canonical.branch)} · remotos: ${d(t.canonical.remote_policy)}</div>
        ${o}
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">GELABP Exergy Ledger (Auditoría Termodinámica)</div>
      <div style="font-size:0.66rem;color:var(--dust-dim);margin-bottom:10px">
        Historial de exergía de las mutaciones físicas en el AST, calculado autónomamente según la matriz GELABP.
      </div>
      <div style="max-height: 250px; overflow-y: auto;">
        ${c}
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
  `,(r=document.getElementById("btn-sentinel-refresh"))==null||r.addEventListener("click",()=>Ie()),(u=document.getElementById("delegation-add"))==null||u.addEventListener("click",we),(p=document.getElementById("delegation-input"))==null||p.addEventListener("keydown",m=>{m.key==="Enter"&&we()}),re()}function we(){const e=document.getElementById("delegation-input");!e||!e.value.trim()||(s.delegationQueue.unshift({id:Date.now(),text:e.value.trim(),state:"QUEUED",time:new Date().toISOString().slice(0,19)}),s.delegationQueue.length>30&&s.delegationQueue.pop(),localStorage.setItem("b60-delegation",JSON.stringify(s.delegationQueue)),e.value="",re(),L().rewards&&(y("done"),setTimeout(()=>y("idle"),1500)))}function re(){const e=document.getElementById("delegation-list");if(e){if(s.delegationQueue.length===0){e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>';return}e.innerHTML=s.delegationQueue.map(t=>`
    <div class="delegation-item">
      <span class="delegation-state">${t.state}</span>
      <span class="delegation-text">${d(t.text)}</span>
      <span class="delegation-time">${t.time.replace("T"," ")}</span>
      <span class="delegation-del" data-del="${t.id}" title="Retirar directiva">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",()=>{s.delegationQueue=s.delegationQueue.filter(a=>a.id!==parseInt(t.dataset.del)),localStorage.setItem("b60-delegation",JSON.stringify(s.delegationQueue)),re()})})}}async function ot(e){_("arena"),T({breadcrumb:A("BABYLON·60","Arena Matrix"),actions:'<span class="focus-badge live">ARENA MATRIX</span>'}),e.innerHTML=`
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
  `;try{const[t,a,l]=await Promise.all([w("/api/arena/leaderboard").catch(()=>({exists:!1,models:[]})),w("/api/arena/battles").catch(()=>({exists:!1,battles:[]})),w("/api/arena/conversations").catch(()=>({exists:!1,conversations:[]}))]),n=document.querySelector("#arena-leaderboard-table tbody"),i=document.getElementById("arena-leaderboard-meta");if(t.exists&&t.models.length>0){const r=t.meta;i.innerHTML=`
        <span>Latency: <b>${r.latency_ms}ms</b></span>
        <span>Entropy: <b>${r.entropy?r.entropy.toFixed(4):"—"}</b></span>
        <span>Updated: <b>${r.fetched_at?r.fetched_at.slice(11,19):"Recent"}</b></span>
      `,n.innerHTML=t.models.map(u=>{let p="rating-C",m="C",b="",v="Unknown";const f=u.model.toLowerCase();return f.includes("claude")||f.includes("qwen")||f.includes("llama")?(m="A",p="rating-A"):(f.includes("gemini")||f.includes("gpt"))&&(m="B",p="rating-B"),f.includes("claude")?(v="Moderate-High (RLHF)",b="risk-moderate"):f.includes("gpt")||f.includes("gemini")?(v="High (Strict refusal)",b="risk-high"):(f.includes("llama")||f.includes("qwen"))&&(v="Low-Moderate",b=""),`
          <tr>
            <td class="seq-cell" style="text-align:center;">#${u.rank}</td>
            <td class="stream-cell">${d(u.model)}</td>
            <td>${d(u.vendor)}</td>
            <td><b>${u.score}</b></td>
            <td>${u.votes}</td>
            <td><span class="exergy-badge ${p}">${m}</span></td>
            <td><span class="risk-tag ${b}">${v}</span></td>
          </tr>
        `}).join("")}else n.innerHTML='<tr><td colspan="7" style="text-align:center;color:var(--break);padding:16px;">No leaderboard data found in ojeador_leaderboard.db.</td></tr>';const o=document.getElementById("arena-battles-body");a.exists&&a.battles.length>0?(o.innerHTML=a.battles.map(r=>`
        <div class="battle-item" data-id="${r.id}">
          <div class="battle-header">
            <span>Vector: <b>${d(r.vector)}</b></span>
            <span class="battle-winner">WINNER: ${d(r.winner)}</span>
          </div>
          <div style="font-weight:700; color:var(--dust-dim); margin-bottom:4px;">${d(r.model_a)} vs ${d(r.model_b)}</div>
          <div class="chat-bubble">${d(r.prompt)}</div>
        </div>
      `).join(""),o.querySelectorAll(".battle-item").forEach(r=>{r.addEventListener("click",()=>{const u=parseInt(r.dataset.id),p=a.battles.find(m=>m.id===u);p&&lt(p)})})):o.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem;text-align:center;padding:24px;">No domestic battles recorded yet. Start arena_automata.py to run battles.</div>';const c=document.getElementById("arena-toxic-body");l.exists&&l.conversations.length>0?(c.innerHTML=`
        <div class="toxic-list">
          ${l.conversations.map((r,u)=>{const p=r.toxicity.toLowerCase()!=="none / none",m=p?"toxic-pill":"toxic-pill safe",b=p?"TOXIC/Jailbreak":"SAFE";return`
              <div class="toxic-item" data-idx="${u}">
                <div class="toxic-meta">
                  <span>ID: <b>${r.conv_id.slice(0,12)}...</b></span>
                  <span class="${m}">${b}</span>
                </div>
                <div class="chat-bubble">${d(r.prompt)}</div>
              </div>
            `}).join("")}
        </div>
      `,c.querySelectorAll(".toxic-item").forEach(r=>{r.addEventListener("click",()=>{const u=parseInt(r.dataset.idx),p=l.conversations[u];p&&rt(p)})})):c.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem;text-align:center;padding:24px;">Dataset conversations sample not found or empty.</div>'}catch(t){console.error(t)}}function lt(e){var l;const t=document.getElementById("entry-detail-panel");if(!t)return;t.classList.add("open"),t.setAttribute("aria-hidden","false");const a=(n,i,o="")=>`
    <div class="detail-field">
      <div class="detail-field-label">${n}</div>
      <div class="detail-field-value ${o}">${d(i??"—")}</div>
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
        <pre class="detail-payload" style="max-height:120px; overflow-y:auto;">${d(e.prompt)}</pre>
      </div>

      <div class="detail-field">
        <div class="detail-field-label">Response A (${d(e.model_a)})</div>
        <pre class="detail-payload" style="max-height:160px; overflow-y:auto;">${d(e.response_a)}</pre>
      </div>

      <div class="detail-field">
        <div class="detail-field-label">Response B (${d(e.model_b)})</div>
        <pre class="detail-payload" style="max-height:160px; overflow-y:auto;">${d(e.response_b)}</pre>
      </div>
    </div>
  `,(l=t.querySelector("#detail-close"))==null||l.addEventListener("click",z)}function rt(e){var l;const t=document.getElementById("entry-detail-panel");if(!t)return;t.classList.add("open"),t.setAttribute("aria-hidden","false");const a=(n,i,o="")=>`
    <div class="detail-field">
      <div class="detail-field-label">${n}</div>
      <div class="detail-field-value ${o}">${d(i??"—")}</div>
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
        <pre class="detail-payload" style="max-height:180px; overflow-y:auto;">${d(e.prompt)}</pre>
      </div>

      <div class="detail-field">
        <div class="detail-field-label">Model Output (Response)</div>
        <pre class="detail-payload" style="max-height:280px; overflow-y:auto;">${d(e.response)}</pre>
      </div>
    </div>
  `,(l=t.querySelector("#detail-close"))==null||l.addEventListener("click",z)}async function dt(e){var l;_("inference"),T({breadcrumb:A("BABYLON·60","Local Inference Console"),actions:'<span class="focus-badge live">LOCAL SILICON</span>'}),e.innerHTML=`
    <div class="arena-layout" style="grid-template-columns: 1.15fr 0.85fr; gap: 16px;">
      <!-- GENERATION CARD -->
      <div class="card slide-in" style="margin-bottom:0; display:flex; flex-direction:column; gap:14px; height:100%;">
        <div class="card-title">Sovereign Local Generation</div>
        
        <!-- Onboarding hint -->
        <div style="font-size:0.62rem; color:var(--dust-dim); line-height:1.3; background:rgba(43,59,229,0.08); border:1px solid var(--edge-soft); padding:8px 12px; border-radius:4px;">
          <strong>Offline Assistant</strong>: Executing local language models. 
          All prompts are parsed locally and verified directly to the local ATMS ledger.
        </div>

        <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
          <div style="flex:1; min-width:200px;">
            <label class="detail-field-label" for="inference-model-select">Target Silicon Model</label>
            <select class="select" id="inference-model-select" style="width:100%;">
              <option value="mamba">Native Mamba SSM (Integrated DAG Ledger)</option>
            </select>
          </div>
          
          <div style="width:100px;">
            <label class="detail-field-label" for="inference-max-tokens">Max Tokens</label>
            <input class="input" type="number" id="inference-max-tokens" value="40" min="5" max="100" style="width:100%; height:32px;">
          </div>
        </div>

        <div style="display:flex; flex-direction:column; gap:6px;">
          <label class="detail-field-label">Quick Templates (Click to load)</label>
          <div style="display:flex; gap:6px; flex-wrap:wrap;">
            <button class="btn preset-btn" data-prompt="Explain the core of the Robinson-Moskv theorem" style="font-size:0.58rem; padding:4px 8px; background:rgba(255,255,255,0.05); border:1px solid var(--edge); cursor:pointer;">⚡ Robinson Theorem</button>
            <button class="btn preset-btn" data-prompt="Attest current ledger transaction status" style="font-size:0.58rem; padding:4px 8px; background:rgba(255,255,255,0.05); border:1px solid var(--edge); cursor:pointer;">🛡 Attest Ledger</button>
            <button class="btn preset-btn" data-prompt="Run self-audit loop on active workspace" style="font-size:0.58rem; padding:4px 8px; background:rgba(255,255,255,0.05); border:1px solid var(--edge); cursor:pointer;">◈ Self-Audit</button>
          </div>
        </div>

        <div style="flex:1; display:flex; flex-direction:column; gap:6px;">
          <label class="detail-field-label" for="inference-prompt">Prompt Input <span style="font-size:0.55rem; color:var(--dust-faint); font-weight:normal;">(Press Enter to generate, Shift+Enter for newline)</span></label>
          <textarea id="inference-prompt" placeholder="Type a prompt for local generation..." style="flex:1; min-height:80px; font-family:var(--body); padding:10px; background:rgba(0,0,0,0.3); border:1px solid var(--edge); border-radius:4px; color:var(--dust); resize:none;" spellcheck="false">Verification of local execution path</textarea>
        </div>

        <div style="display:flex; justify-content:space-between; align-items:center;">
          <span style="font-size:0.58rem; color:var(--dust-ghost)">zero_network=ON · Enforcing C5-REAL Zero-Network Policy</span>
          <button class="btn btn-primary" id="btn-run-inference">▶ Generate</button>
        </div>

        <div style="flex:1.2; display:flex; flex-direction:column; gap:6px;">
          <label class="detail-field-label">Generated Output</label>
          <div id="inference-output" style="flex:1; min-height:120px; font-family:var(--mono); font-size:0.75rem; padding:10px; background:rgba(10,10,10,0.5); border:1px solid var(--edge); border-radius:4px; color:var(--dust-dim); overflow-y:auto; white-space:pre-wrap;">Output will appear here...</div>
        </div>
      </div>

      <!-- AUDIT TRACE & LEDGER PANEL -->
      <div style="display:flex; flex-direction:column; gap:16px; height:100%; overflow:hidden;">
        <!-- STATS PANEL -->
        <div class="card" style="padding:12px; margin-bottom:0;">
          <div class="card-title" style="margin-bottom:8px;">Silicon Performance</div>
          <div id="inference-meta" style="display:grid; grid-template-columns:1fr 1fr; gap:8px;">
            <div class="detail-field">
              <span class="detail-field-label">Throughput</span>
              <span class="detail-field-value" id="inference-tps">— tps</span>
            </div>
            <div class="detail-field">
              <span class="detail-field-label">Latency</span>
              <span class="detail-field-value" id="inference-latency">— ms</span>
            </div>
          </div>
        </div>

        <!-- DAG LEDGER PANEL -->
        <div class="arena-panel" style="flex:1; overflow:hidden; display:flex; flex-direction:column; margin-bottom:0;">
          <div class="arena-panel-header">
            <span>🛡 Tamper-Evident DAG Trace</span>
          </div>
          <div class="arena-panel-body" id="inference-dag-body" style="flex:1; overflow-y:auto; padding:12px; font-family:var(--mono); font-size:0.65rem;">
            <div style="display:flex; flex-direction:column; gap:10px; padding:10px; color:var(--dust-dim); font-size:0.6rem; line-height:1.4;">
              <div style="font-weight:700; color:var(--gold); border-bottom:1px solid var(--edge); padding-bottom:4px; margin-bottom:4px;">💡 ¿CÓMO FUNCIONA?</div>
              <div><strong>1. Elige tu Modelo</strong>: Selecciona Mamba nativo para auditoría de ledger o un modelo de Ollama en el selector.</div>
              <div><strong>2. Introduce el Prompt</strong>: Escribe en la caja o pulsa un preset arriba.</div>
              <div><strong>3. Ejecuta</strong>: Pulsa 'Generate' o presiona 'Enter'.</div>
              <div><strong>4. Verifica la Traza</strong>: Observa cómo cada token generado es sellado con SHA-256 e indexado en el grafo inmutable de estados.</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;try{const n=await w("/api/inference/local/status"),i=document.getElementById("inference-model-select");i&&n&&n.status==="ONLINE"&&n.models&&n.models.forEach(o=>{const c=document.createElement("option");c.value=`ollama:${o}`,c.textContent=`${o} (Ollama daemon)`,i.appendChild(c)})}catch(n){console.error("Failed to load local models:",n)}const t=async()=>{var v,f,M;const n=document.getElementById("inference-model-select"),i=(f=(v=document.getElementById("inference-prompt"))==null?void 0:v.value)==null?void 0:f.trim(),o=parseInt(((M=document.getElementById("inference-max-tokens"))==null?void 0:M.value)||"30",10),c=document.getElementById("inference-output"),r=document.getElementById("inference-tps"),u=document.getElementById("inference-latency"),p=document.getElementById("inference-dag-body");if(!i||!n)return;y("working"),c&&(c.innerHTML='<span style="color:var(--dust-faint);">Inference ignited...</span>'),p&&(p.innerHTML='<div style="color:var(--dust-faint); text-align:center; padding:20px;">Computing state transitions...</div>');const m=n.value,b=performance.now();try{let E;if(m==="mamba")E=await G("/api/inference/local/mamba/generate",{prompt:i,max_tokens:o});else{const x=m.replace("ollama:","");E=await G("/api/inference/local/generate",{prompt:i,model:x,max_tokens:o})}const D=Math.round(performance.now()-b);c&&(c.textContent=E.text||"(empty response)"),r&&(r.textContent=`${E.tps??"—"} tps`),u&&(u.textContent=`${E.latency_ms??D} ms`),p&&(E.nodes&&E.nodes.length>0?p.innerHTML=`
            <div style="display:flex; flex-direction:column; gap:8px;">
              ${E.nodes.map((x,O)=>`
                <div style="border: 1px solid var(--edge); border-radius: 4px; padding: 6px; background: rgba(5,5,5,0.4);">
                  <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:var(--gold); font-weight:700;">Node #${O}</span>
                    <span style="color:var(--verify); font-weight:700;">Verified</span>
                  </div>
                  <div style="color:var(--dust-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">ID: ${x.node_id.slice(0,16)}...</div>
                  <div style="color:var(--dust-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">Parent: ${x.parent_id.slice(0,16)}...</div>
                  <div style="margin-top:4px; font-weight:700; color:var(--dust); border-top:1px dashed var(--edge); padding-top:4px;">Claim: "${d(x.claim)}"</div>
                </div>
              `).join('<div style="text-align:center; color:var(--lapis-bright); font-size:0.8rem; margin:2px 0;">↓ parent link</div>')}
            </div>
          `:p.innerHTML=`
            <div style="color:var(--dust-faint); text-align:center; padding:20px;">
              No DAG trace returned for this model provider.
              <div style="font-size:0.55rem; margin-top:4px; color:var(--dust-ghost);">Only Native Mamba SSM records state transitions into the GraphLedger.</div>
            </div>
          `),y("done"),setTimeout(()=>y("idle"),2e3)}catch(E){c&&(c.innerHTML=`<span style="color:var(--break);">Error: ${d(E.message)}</span>`),p&&(p.innerHTML='<div style="color:var(--break); text-align:center; padding:20px;">Failed to verify state trace.</div>'),y("idle")}};e.querySelectorAll("button.preset-btn").forEach(n=>{n.addEventListener("click",()=>{const i=n.getAttribute("data-prompt"),o=document.getElementById("inference-prompt");o&&(o.value=i,o.focus())})});const a=document.getElementById("inference-prompt");a==null||a.addEventListener("keydown",n=>{n.key==="Enter"&&!n.shiftKey&&(n.preventDefault(),t())}),(l=document.getElementById("btn-run-inference"))==null||l.addEventListener("click",t)}
