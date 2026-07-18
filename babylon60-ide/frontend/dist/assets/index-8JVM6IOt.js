(function(){const t=document.createElement("link").relList;if(t&&t.supports&&t.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))i(s);new MutationObserver(s=>{for(const o of s)if(o.type==="childList")for(const l of o.addedNodes)l.tagName==="LINK"&&l.rel==="modulepreload"&&i(l)}).observe(document,{childList:!0,subtree:!0});function a(s){const o={};return s.integrity&&(o.integrity=s.integrity),s.referrerPolicy&&(o.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?o.credentials="include":s.crossOrigin==="anonymous"?o.credentials="omit":o.credentials="same-origin",o}function i(s){if(s.ep)return;s.ep=!0;const o=a(s);fetch(s.href,o)}})();const we="";async function $(e){const t=await fetch(`${we}${e}`);if(!t.ok){const a=await t.json().catch(()=>({detail:t.statusText}));throw new Error(a.detail||t.statusText)}return t.json()}async function G(e,t){const a=await fetch(`${we}${e}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(t)});if(!a.ok){const i=await a.json().catch(()=>({detail:a.statusText}));throw new Error(i.detail||a.statusText)}return a.json()}function ke(e,t,a){const i=location.protocol==="https:"?"wss:":"ws:",s={closed:!1,ws:null},o=()=>{if(s.closed)return;const l=new WebSocket(`${i}//${location.host}${e}`);s.ws=l,l.onmessage=p=>{let d;try{d=JSON.parse(p.data)}catch{return}t(d)},l.onerror=p=>a==null?void 0:a(p),l.onclose=()=>{s.closed||setTimeout(o,3e3)}};return s.close=()=>{var l;s.closed=!0;try{(l=s.ws)==null||l.close()}catch{}},o(),s}const D={};let j=null;function _(e,t){D[e]=t}function x(e){if(j===e)return;j=e,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===e)});const t=document.getElementById("main-content");D[e]&&(t.innerHTML="",D[e](t)),history.replaceState(null,"",`#${e}`)}function Ie(){const e=document.getElementById("main-content");j&&D[j]&&e&&(e.innerHTML="",D[j](e))}function Me(){const e=location.hash.replace("#","");return e&&D[e]?e:"ledger"}const Z={"2e":{key:"2e",label:"2E ◐",name:"Doble Excepcionalidad (TDAH + AACC)",tachometer:!0,loopGuard:!0,restoreBanner:!0,rewards:!0,spineLabels:!1},nt:{key:"nt",label:"NT ○",name:"Neurotípico",tachometer:!1,loopGuard:!1,restoreBanner:!1,rewards:!1,spineLabels:!0}};function w(){return Z[n.cognitiveMode]||Z["2e"]}function Ee(e){try{const t=JSON.parse(e||"[]");return Array.isArray(t)?t:[]}catch{return[]}}const n={cognitiveMode:localStorage.getItem("b60-cogmode")||"2e",contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:Ee(localStorage.getItem("b60-scratch")),delegationQueue:Ee(localStorage.getItem("b60-delegation")),databaseList:[],ledgerStats:null,lastVerify:null,sentinel:null,sentinelModalShown:!1,telemetrySnapshot:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasVB:{x:80,y:40,w:720,h:400},canvasAbort:null};document.addEventListener("DOMContentLoaded",async()=>{Se(n.cognitiveMode,{silent:!0}),b("indexing"),Be(),Oe(),qe(),Ve(),Qe(),Ue(),Ne(),Ce(),Ge(),await Promise.all([Ae(),Ye(),De()]),se(),V(),b("done"),w().restoreBanner&&Fe(localStorage.getItem("b60-route")||"ledger"),x(Me()),b("idle")});function Se(e,{silent:t=!1}={}){n.cognitiveMode=Z[e]?e:"2e",localStorage.setItem("b60-cogmode",n.cognitiveMode),document.body.classList.toggle("mode-2e",n.cognitiveMode==="2e"),document.body.classList.toggle("mode-nt",n.cognitiveMode==="nt");const a=document.getElementById("btn-cogmode");a&&(a.textContent=w().label,a.title=`Modo cognitivo: ${w().name} — click o ⌘⇧E para alternar`),t||(Be(),Ie(),Y({icon:w().key==="2e"?"◐":"○",message:`Modo cognitivo: ${w().name}. ${w().key==="2e"?"Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos.":"Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."}`}),setTimeout(T,3e3))}function ae(){Se(n.cognitiveMode==="2e"?"nt":"2e")}function Ce(){var t;let e=document.getElementById("btn-cogmode");if(!e){const a=(t=document.getElementById("btn-bifocal"))==null?void 0:t.parentElement;if(a){const i=document.createElement("div");i.className="status-segment",i.innerHTML='<button class="status-bifocal" id="btn-cogmode"></button>',a.parentElement.insertBefore(i,a),e=i.querySelector("#btn-cogmode")}}e&&(e.textContent=w().label,e.title=`Modo cognitivo: ${w().name} — click o ⌘⇧E para alternar`,e.addEventListener("click",ae))}function b(e){n.tachometerState=e;const t=document.getElementById("tachometer");t&&(t.className=`tachometer ${e!=="idle"?e:""}`);const a=document.getElementById("status-agent-segment");if(a)if(e==="working"||e==="indexing"){a.style.display="flex";const i=document.getElementById("status-agent-text");i&&(i.textContent=e==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}const _e=[{id:"canvas",icon:"⬡",label:"Canvas",tip:"Architecture Canvas — ABSTRAER  ⌘5"},{id:"ledger",icon:"⧉",label:"Ledger",tip:"BFT Ledger — DETERMINAR  ⌘1"},{id:"databases",icon:"⛁",label:"Ontologies",tip:"Ontologies (explorador SQLite)  ⌘2"},{id:"query",icon:"❯_",label:"SQL",tip:"SQL Console (solo lectura)  ⌘3"},{id:"swarm",icon:"⚡",label:"Swarm",tip:"Agent Swarm (telemetría en vivo)  ⌘4"},{id:"sentinel",icon:"⎇",label:"Sentinel",tip:"Git Sentinel (identidad de repo + delegación)  ⌘6"},{id:"arena",icon:"⚔",label:"Arena",tip:"Arena Matrix (Chatbot Arena)  ⌘7"},{id:"inference",icon:"◈",label:"Inference",tip:"Local Inference Console — ⌘8"}];function Be(){const e=document.getElementById("spine");if(!e)return;e.innerHTML="";const t=document.createElement("div");t.className="spine-logo",t.title="BABYLON·60 v1.1.0",t.innerHTML='<div class="spine-logo-dot"></div>',e.appendChild(t);const a=w().spineLabels;_e.forEach((i,s)=>{if(s===1){const l=document.createElement("div");l.className="spine-separator",e.appendChild(l)}const o=document.createElement("button");o.className="spine-icon",o.dataset.route=i.id,a||(o.dataset.tooltip=i.tip),o.setAttribute("aria-label",i.tip),o.innerHTML=a?`<span class="spine-glyph">${i.icon}</span><span class="spine-label">${i.label}</span>`:i.icon,o.addEventListener("click",()=>x(i.id)),e.appendChild(o)}),Te(n.activeRoute)}function Te(e){document.querySelectorAll(".spine-icon").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function Oe(){var e;(e=document.getElementById("btn-collapse-ctx"))==null||e.addEventListener("click",ne),V()}function ne(){n.contextPaneOpen=!n.contextPaneOpen;const e=document.getElementById("context-pane"),t=document.getElementById("btn-collapse-ctx");e&&(e.classList.toggle("collapsed",!n.contextPaneOpen),t&&(t.textContent=n.contextPaneOpen?"⟨":"⟩"))}function V(){var i,s,o,l,p;const e=document.getElementById("context-pane-body");if(!e)return;const t=n.databaseList.slice(0,5).map(d=>`
    <div class="ctx-item depth-1" data-goto-db="${r(d.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${r(d.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `).join(""),a=(s=(i=n.sentinel)==null?void 0:i.warnings)!=null&&s.some(d=>d.level==="red")?'<span class="ctx-item-badge break">!</span>':(l=(o=n.sentinel)==null?void 0:o.warnings)!=null&&l.length?'<span class="ctx-item-badge gold">△</span>':'<span class="ctx-item-badge verify">ok</span>';e.innerHTML=`
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
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${((p=n.ledgerStats)==null?void 0:p.entries)??"—"}</span>
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
  `,e.querySelectorAll(".ctx-item[data-route]").forEach(d=>{d.addEventListener("click",()=>x(d.dataset.route))}),e.querySelectorAll(".ctx-item[data-goto-db]").forEach(d=>{d.addEventListener("click",()=>x("databases"))})}function U(){var a;const e=document.getElementById("ctx-db-count");e&&(e.textContent=n.databaseList.length||"—");const t=document.getElementById("ctx-ledger-count");t&&(t.textContent=((a=n.ledgerStats)==null?void 0:a.entries)??"—")}function He(e){document.querySelectorAll(".ctx-item[data-route]").forEach(t=>{t.classList.toggle("active",t.dataset.route===e)})}function se(){var l,p,d;const e=document.getElementById("status-conn-dot"),t=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),i=document.getElementById("status-ledger-entries"),s=document.getElementById("status-lamport"),o=n.ledgerStats!==null||n.databaseList.length>0;e&&(e.className=o?"status-dot":"status-dot error"),t&&(t.textContent=o?"CONNECTED":"OFFLINE"),a&&(a.textContent=n.databaseList.length||"—"),i&&(i.textContent=((l=n.ledgerStats)==null?void 0:l.entries)??"—"),s&&(s.textContent=((d=(p=n.ledgerStats)==null?void 0:p.latest)==null?void 0:d.lamport_t)!=null?`L:${n.ledgerStats.latest.lamport_t}`:"—"),ie()}function ie(){var o,l;let e=document.getElementById("status-repo-segment");if(!e){const p=document.getElementById("status-bar"),d=p==null?void 0:p.querySelector(".status-segment");if(!p||!d)return;e=document.createElement("div"),e.className="status-segment",e.id="status-repo-segment",e.style.cursor="pointer",e.innerHTML='<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>',d.after(e),e.addEventListener("click",()=>x("sentinel"))}const t=document.getElementById("status-repo-text");if(!t)return;const a=n.sentinel;if(!a){t.textContent="—";return}const i=(o=a.warnings)==null?void 0:o.some(p=>p.level==="red"),s=!i&&((l=a.warnings)==null?void 0:l.length)>0;t.textContent=`${a.repo_name}${a.branch?" @"+a.branch:""}${a.head?" · "+a.head:""}${i?" ⚠":s?" △":" ✓"}`,t.style.color=i?"var(--break)":s?"var(--gold)":"var(--verify)",e.title=i?"LINAJE NO CANÓNICO — abre Git Sentinel":s?"Avisos de linaje — abre Git Sentinel":`Linaje canónico verificado (${a.commit_count??"—"} commits)`}async function De(){var e;try{n.sentinel=await $("/api/sentinel/status"),ie();const t=((e=n.sentinel.warnings)==null?void 0:e.filter(a=>a.level==="red"))||[];t.length>0&&!n.sentinelModalShown&&(n.sentinelModalShown=!0,Y({icon:"⚠",message:`GIT SENTINEL: ${t[0].msg}`,actions:[{label:"Abrir Sentinel",primary:!0,fn:()=>{T(),x("sentinel")}},{label:"Entendido",fn:T}]}))}catch{}}function Ne(){var e;(e=document.getElementById("btn-bifocal"))==null||e.addEventListener("click",le)}function le(){n.bifocalMode=n.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",n.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",n.bifocalMode==="micro");const e=document.getElementById("btn-bifocal");e&&(e.textContent=n.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),n.bifocalMode==="macro"&&x("canvas")}const F=[{icon:"⬡",label:"Architecture Canvas",desc:"ABSTRAER: ver el sistema completo",shortcut:"⌘5",action:()=>x("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"DETERMINAR: inspector de cadena de hashes",shortcut:"⌘1",action:()=>x("ledger")},{icon:"⛁",label:"Ontologies",desc:"Explorador SQLite (solo lectura)",shortcut:"⌘2",action:()=>x("databases")},{icon:"❯_",label:"SQL Console",desc:"Consultas read-only contra cualquier .db",shortcut:"⌘3",action:()=>x("query")},{icon:"⚡",label:"Agent Swarm",desc:"Telemetría en vivo (push WS, sin polling)",shortcut:"⌘4",action:()=>x("swarm")},{icon:"⎇",label:"Git Sentinel",desc:"Identidad de repo + delegación de mutaciones git",shortcut:"⌘6",action:()=>x("sentinel")},{icon:"⚿",label:"Verify Chain Integrity",desc:"Recomputar SHA3-256 de toda la cadena",shortcut:"",action:()=>{x("ledger"),setTimeout(()=>{var e;return(e=document.getElementById("btn-verify-chain"))==null?void 0:e.click()},400)}},{icon:"◐",label:"Toggle Cognitive Mode",desc:"Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",shortcut:"⌘⇧E",action:ae},{icon:"⟨",label:"Toggle Context Pane",desc:"Mostrar / ocultar mapa semántico",shortcut:"⌘B",action:ne},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Alternar vista bifocal",shortcut:"⌘M",action:le},{icon:"◎",label:"Open Scratchpad",desc:"Volcar un pensamiento sin perder foco",shortcut:"⌘⇧Space",action:()=>q(!0)}];let S=0,C=[...F];function qe(){const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.addEventListener("click",a=>{a.target===e&&N()}),t.addEventListener("input",()=>Pe(t.value)),t.addEventListener("keydown",je))}function Re(){n.paletteOpen=!0;const e=document.getElementById("palette-overlay"),t=document.getElementById("palette-input");!e||!t||(e.classList.add("visible"),e.setAttribute("aria-hidden","false"),t.value="",S=0,C=[...F],Q(),setTimeout(()=>t.focus(),50))}function N(){n.paletteOpen=!1;const e=document.getElementById("palette-overlay");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true"))}function Pe(e){const t=e.toLowerCase().trim();S=0,C=t?F.filter(a=>a.label.toLowerCase().includes(t)||a.desc.toLowerCase().includes(t)):[...F],Q(t)}function ze(e){return e.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}function Q(e=""){const t=document.getElementById("palette-results");if(t){if(C.length===0){t.innerHTML=`<div class="palette-empty">No commands match "<strong>${r(e)}</strong>"</div>`;return}t.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${C.map((a,i)=>{const s=e?a.label.replace(new RegExp(`(${ze(e)})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${i===S?"selected":""}" data-index="${i}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${s}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,t.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const i=parseInt(a.dataset.index);C[i]&&(C[i].action(),N())}),a.addEventListener("mouseenter",()=>{S=parseInt(a.dataset.index),t.querySelectorAll(".palette-item").forEach((i,s)=>i.classList.toggle("selected",s===S))})})}}function je(e){var t,a;if(e.key==="Escape"){N();return}e.key==="ArrowDown"&&(e.preventDefault(),S=Math.min(S+1,C.length-1),Q(((t=document.getElementById("palette-input"))==null?void 0:t.value)||"")),e.key==="ArrowUp"&&(e.preventDefault(),S=Math.max(S-1,0),Q(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),e.key==="Enter"&&(e.preventDefault(),C[S]&&(C[S].action(),N()))}function Ve(){var a,i;const e=document.getElementById("scratchpad-modal"),t=document.getElementById("scratchpad-input");!e||!t||((a=document.getElementById("scratchpad-save"))==null||a.addEventListener("click",$e),(i=document.getElementById("scratchpad-close"))==null||i.addEventListener("click",()=>q(!1)),t.addEventListener("keydown",s=>{s.key==="Enter"&&!s.shiftKey&&(s.preventDefault(),$e()),s.key==="Escape"&&q(!1)}),oe())}function q(e){const t=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");t&&(n.scratchpadOpen=e!==void 0?e:!n.scratchpadOpen,t.classList.toggle("visible",n.scratchpadOpen),t.setAttribute("aria-hidden",String(!n.scratchpadOpen)),n.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}function $e(){const e=document.getElementById("scratchpad-input");if(!e||!e.value.trim())return;const t={id:Date.now(),text:e.value.trim(),time:new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})};n.scratchpadItems.unshift(t),n.scratchpadItems.length>20&&n.scratchpadItems.pop(),localStorage.setItem("b60-scratch",JSON.stringify(n.scratchpadItems)),e.value="",oe(),V(),w().rewards&&(b("done"),setTimeout(()=>b("idle"),2e3))}function oe(){const e=document.getElementById("scratchpad-items");if(e){if(n.scratchpadItems.length===0){e.innerHTML="";return}e.innerHTML=n.scratchpadItems.map(t=>`
    <div class="scratchpad-item" data-id="${t.id}">
      <span class="scratchpad-item-time">${t.time}</span>
      <span class="scratchpad-item-text">${r(t.text)}</span>
      <span class="scratchpad-item-del" data-del="${t.id}" title="Remove">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",a=>{a.stopPropagation();const i=parseInt(t.dataset.del);n.scratchpadItems=n.scratchpadItems.filter(s=>s.id!==i),localStorage.setItem("b60-scratch",JSON.stringify(n.scratchpadItems)),oe(),V()})})}}function Y({icon:e="⬡",message:t,actions:a=[]}){const i=document.getElementById("agent-modal"),s=document.getElementById("agent-modal-icon"),o=document.getElementById("agent-modal-msg"),l=document.getElementById("agent-modal-actions");if(!i||!o||!l)return;s&&(s.textContent=e),o.textContent=t;const p=a.length>0?a:[{label:"Got it",fn:T,primary:!0}];l.innerHTML=p.map((d,c)=>`<button class="btn ${d.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${c}">${d.label}</button>`).join(""),l.querySelectorAll("button").forEach(d=>{d.addEventListener("click",()=>{var c,m;return(m=(c=p[parseInt(d.dataset.actionIdx)])==null?void 0:c.fn)==null?void 0:m.call(c)})}),i.classList.add("visible"),i.setAttribute("aria-hidden","false"),w().tachometer&&b("alert")}function T(){const e=document.getElementById("agent-modal");e&&(e.classList.remove("visible"),e.setAttribute("aria-hidden","true")),b("idle")}function Ge(){setInterval(()=>{if(!w().loopGuard||!n.loopDetector.route||n.loopDetector.interventionFired)return;if(Date.now()-n.loopDetector.routeEnteredAt>1500*1e3){n.loopDetector.interventionFired=!0;const t=n.loopDetector.route;Y({icon:"⏱",message:`Llevas más de 25 minutos en ${t.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,actions:[{label:"Ver Arquitectura",primary:!0,fn:()=>{T(),x("canvas")}},{label:"Sigo aquí",fn:T},{label:"Volcar idea →",fn:()=>{T(),q(!0)}}]})}},120*1e3)}function Fe(e){var p;const t=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),i=document.getElementById("restore-points"),s=document.getElementById("restore-dismiss");if(!t||!a)return;const l=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas",sentinel:"Git Sentinel"}[e]||e}`,`${n.databaseList.length||"—"} databases available`,((p=n.ledgerStats)==null?void 0:p.entries)!=null?`${n.ledgerStats.entries} ledger entries`:"Ledger loading...",n.sentinel?`repo ${n.sentinel.repo_name}@${n.sentinel.branch??"—"}`:""].filter(Boolean);a.textContent="Session restored · ",i&&(i.innerHTML=l.map(d=>`<span class="restore-point">${r(d)}</span>`).join("")),t.style.display="flex",s==null||s.addEventListener("click",()=>{t.style.display="none"}),setTimeout(()=>{t.style.display="none"},12e3)}function Qe(){const e={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas",6:"sentinel",7:"arena",8:"inference"};window.addEventListener("keydown",t=>{const a=t.metaKey||t.ctrlKey;if(a&&t.key==="k"&&!t.shiftKey){t.preventDefault(),n.paletteOpen?N():Re();return}if(a&&t.shiftKey&&t.code==="Space"){t.preventDefault(),q();return}if(a&&t.shiftKey&&(t.key==="e"||t.key==="E")){t.preventDefault(),ae();return}if(a&&t.key==="b"&&!t.shiftKey){t.preventDefault(),ne();return}if(a&&t.key==="m"&&!t.shiftKey){t.preventDefault(),le();return}if(a&&e[t.key]){t.preventDefault(),x(e[t.key]);return}if(t.key==="Escape"){if(n.paletteOpen){N();return}if(n.scratchpadOpen){q(!1);return}R()}})}function Ue(){_("canvas",Ke),_("ledger",We),_("databases",Xe),_("query",tt),_("swarm",at),_("sentinel",it),_("arena",lt),_("inference",rt),window.addEventListener("hashchange",()=>{const e=window.location.hash.replace("#","");e&&x(e)})}async function Ae(){try{n.databaseList=await $("/api/databases"),U()}catch{}}async function Ye(){try{n.ledgerStats=await $("/api/ledger/stats"),U(),se()}catch{}}function A({breadcrumb:e="",actions:t=""}={}){const a=document.getElementById("focus-breadcrumb"),i=document.getElementById("focus-actions");a&&(a.innerHTML=e),i&&(i.innerHTML=t)}function k(...e){return e.map((t,a)=>a<e.length-1?`<span class="breadcrumb-item">${t}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${t}</span>`).join("")}function O(e){n.activeRoute=e,localStorage.setItem("b60-route",e),Te(e),He(e),R(),e!=="swarm"&&n.telemetrySocket&&(n.telemetrySocket.close(),n.telemetrySocket=null),n.loopDetector.route!==e&&(n.loopDetector.route=e,n.loopDetector.routeEnteredAt=Date.now(),n.loopDetector.interventionFired=!1)}function r(e){return String(e??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Ke(e){var re,ce,pe,me,ue,ve,ge;O("canvas"),A({breadcrumb:k("BABYLON·60","Architecture — ABSTRAER (ver el todo antes que la parte)"),actions:'<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>'});try{n.telemetrySnapshot=await $("/api/telemetry/snapshot")}catch{}const t=n.telemetrySnapshot,a=n.databaseList.length,i=((re=n.ledgerStats)==null?void 0:re.entries)??"—",s=(t==null?void 0:t.total_db_size_mb)!=null?`${t.total_db_size_mb}MB`:"—",o=n.sentinel,l=o!=null&&o.is_git?`${o.repo_name}@${o.branch??"—"} · ${o.head??"—"}`:"no git",p=(ce=o==null?void 0:o.warnings)!=null&&ce.some(g=>g.level==="red")?"err":(pe=o==null?void 0:o.warnings)!=null&&pe.length?"warn":"ok",d=[{id:"frontend",x:140,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:`Vite · modo ${w().key.toUpperCase()}`,status:"ok"},{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"14 endpoints · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger",meta:`${i} entries · SHA3-256 (huella criptográfica)`,status:(me=n.ledgerStats)!=null&&me.exists?"ok":"err",goto:"ledger"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Ontology DBs",meta:`${a} DBs · ${s} · RO`,status:a>0?"ok":"warn",goto:"databases"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:t?"WS push 2s (sin polling)":"offline",status:t?"ok":"warn",goto:"swarm"},{id:"git",x:140,y:240,type:"SENTINEL",name:"Git Sentinel",meta:l,status:p,goto:"sentinel"}],c=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"git",to:"fastapi"}],m={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};e.innerHTML=`
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
  `;const u=document.getElementById("canvas-svg"),y=document.getElementById("canvas-edges"),v=document.getElementById("canvas-nodes");if(!u||!y||!v)return;c.forEach(({from:g,to:h})=>{const I=d.find(W=>W.id===g),z=d.find(W=>W.id===h);if(!I||!z)return;const fe=I.x+90,ye=I.y+35,be=z.x,he=z.y+35,H=document.createElementNS("http://www.w3.org/2000/svg","path"),xe=(fe+be)/2;H.setAttribute("d",`M${fe},${ye} C${xe},${ye} ${xe},${he} ${be},${he}`),H.setAttribute("stroke","var(--edge)"),H.setAttribute("stroke-width","1.5"),H.setAttribute("fill","none"),H.setAttribute("opacity","0.5"),H.setAttribute("marker-end","url(#arrow)"),y.appendChild(H)}),d.forEach(g=>{const h=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");h.setAttribute("x",g.x),h.setAttribute("y",g.y),h.setAttribute("width","195"),h.setAttribute("height","76");const I=document.createElement("div");I.className="canvas-node-card",I.style.position="relative",I.innerHTML=`
      <div class="canvas-node-type">${g.type}</div>
      <div class="canvas-node-name">${g.name}</div>
      <div class="canvas-node-meta">${r(g.meta)}</div>
      <div class="canvas-node-status" style="background:${m[g.status]||m.idle};box-shadow:0 0 5px ${m[g.status]||m.idle}"></div>
    `,g.goto&&I.addEventListener("click",()=>x(g.goto)),h.appendChild(I),v.appendChild(h)});const f=()=>u.setAttribute("viewBox",`${n.canvasVB.x} ${n.canvasVB.y} ${n.canvasVB.w} ${n.canvasVB.h}`),E=()=>{n.canvasVB={x:80,y:40,w:720,h:400},f()};E();const M=g=>{const h=n.canvasVB,I=h.x+h.w/2,z=h.y+h.h/2;h.w=Math.max(200,Math.min(2e3,h.w*g)),h.h=Math.max(110,Math.min(1100,h.h*g)),h.x=I-h.w/2,h.y=z-h.h/2,f()};(ue=document.getElementById("canvas-zoom-in"))==null||ue.addEventListener("click",()=>M(1/1.2)),(ve=document.getElementById("canvas-zoom-out"))==null||ve.addEventListener("click",()=>M(1.2)),(ge=document.getElementById("canvas-fit-btn"))==null||ge.addEventListener("click",E),u.addEventListener("wheel",g=>{g.preventDefault(),M(g.deltaY>0?1.1:1/1.1)},{passive:!1}),n.canvasAbort&&n.canvasAbort.abort(),n.canvasAbort=new AbortController;const B=n.canvasAbort.signal;let L=!1,P=0,K=0;u.addEventListener("pointerdown",g=>{L=!0,P=g.clientX,K=g.clientY}),window.addEventListener("pointermove",g=>{if(!L)return;const h=n.canvasVB.w/u.clientWidth;n.canvasVB.x-=(g.clientX-P)*h,n.canvasVB.y-=(g.clientY-K)*h,P=g.clientX,K=g.clientY,f()},{signal:B}),window.addEventListener("pointerup",()=>{L=!1},{signal:B})}let ee=1;const J=50;async function We(e){var t,a,i,s,o;O("ledger"),A({breadcrumb:k("BABYLON·60","BFT Ledger — DETERMINAR (verificar hasta el hash)"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),(t=document.getElementById("btn-verify-chain"))==null||t.addEventListener("click",Je),e.innerHTML=`
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
  `;try{const l=await $("/api/ledger/stats");n.ledgerStats=l;const p=document.getElementById("stat-db-name");p&&(p.textContent=l.db_path||"—");const d=document.getElementById("stat-total-entries");d&&(d.textContent=l.entries??0);const c=document.getElementById("stat-latest-lamport");c&&(c.textContent=`Lamport (reloj lógico causal): ${((a=l.latest)==null?void 0:a.lamport_t)??"—"}`);const m=document.getElementById("stat-latest-time");m&&((i=l.latest)!=null&&i.created_at)&&(m.textContent=String(l.latest.created_at).slice(0,19)),se(),U()}catch{}await X(1),(s=document.getElementById("btn-ledger-prev"))==null||s.addEventListener("click",()=>X(ee-1)),(o=document.getElementById("btn-ledger-next"))==null||o.addEventListener("click",()=>X(ee+1))}async function X(e){e<1&&(e=1),ee=e;const t=document.getElementById("ledger-table-body");if(t)try{const a=(e-1)*J,i=await $(`/api/ledger/entries?limit=${J}&offset=${a}`),s=i.entries||[],o=i.total??s.length;s.length===0?t.innerHTML='<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>':(t.innerHTML=s.map(m=>`
        <tr data-seq="${m.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${m.seq}</td>
          <td class="stream-cell">${r(m.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${r(m.entity_id)}</td>
          <td>${r(m.event_type)}</td>
          <td style="color:var(--dust-dim)">${m.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${r(m.cortex_taint)}">${r((m.cortex_taint||"—").slice(0,26))}${(m.cortex_taint||"").length>26?"…":""}</td>
          <td class="time-cell">${String(m.created_at||"").slice(0,19)}</td>
          <td class="hash-cell" title="${r(m.entry_hash)}">${(m.entry_hash||"—").slice(0,12)}…</td>
        </tr>
      `).join(""),t.querySelectorAll("tr[data-seq]").forEach(m=>{m.addEventListener("click",()=>te(parseInt(m.dataset.seq)))}));const l=Math.max(1,Math.ceil(o/J)),p=document.getElementById("ledger-page-info");p&&(p.textContent=`Page ${e} / ${l} · ${o} entries`);const d=document.getElementById("btn-ledger-prev"),c=document.getElementById("btn-ledger-next");d&&(d.disabled=e<=1),c&&(c.disabled=e>=l)}catch(a){t.innerHTML=`<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${r(a.message)}</td></tr>`}}async function te(e){var a,i;const t=document.getElementById("entry-detail-panel");if(t){t.classList.add("open"),t.setAttribute("aria-hidden","false"),t.innerHTML=`<div class="detail-header"><span class="detail-title">⧉ Entry #${e}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`,(a=t.querySelector("#detail-close"))==null||a.addEventListener("click",R);try{const s=await $(`/api/ledger/entry/${e}`);let o=s.payload_json||"";try{o=JSON.stringify(JSON.parse(s.payload_json),null,2)}catch{}const l=(p,d,c="")=>`
      <div class="detail-field">
        <div class="detail-field-label">${p}</div>
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
          <pre class="detail-payload">${r(o)}</pre>
        </div>
      </div>
    `,(i=t.querySelector("#detail-close"))==null||i.addEventListener("click",R)}catch(s){const o=t.querySelector(".detail-body");o&&(o.innerHTML=`<span style="color:var(--break)">${r(s.message)}</span>`)}}}function R(){const e=document.getElementById("entry-detail-panel");e&&(e.classList.remove("open"),e.setAttribute("aria-hidden","true"))}async function Je(){const e=document.getElementById("btn-verify-chain"),t=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),i=document.getElementById("verify-progress-bar"),s=document.getElementById("stat-integrity"),o=document.getElementById("verify-summary");if(!t)return;e&&(e.disabled=!0,e.textContent="⚙ Verifying..."),a&&(a.style.display="block"),b("working");let l=0;const p=setInterval(()=>{l=Math.min(l+8,90),i&&(i.style.width=`${l}%`)},120);try{const d=await G("/api/ledger/verify",{});n.lastVerify=d,clearInterval(p),i&&(i.style.width="100%");const c=d.total_entries??0,m=d.verified_entries??0,u=c-m;t.innerHTML="",(d.entries||[]).slice(0,400).forEach(v=>{const f=document.createElement("div");f.className=`chain-block ${v.valid?"":"invalid"}`,f.title=`Seq ${v.seq} · L:${v.lamport_t} · ${v.valid?"VALID":v.errors.join(" · ")}`,f.addEventListener("click",()=>te(v.seq)),t.appendChild(f)}),c===0&&(t.innerHTML='<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>');const y=d.broken_at!=null;if(s&&(s.textContent=d.valid?"VERIFIED":y?`BROKEN (${u})`:"ERROR",s.className=`stat-value ${d.valid?"verify":"break"}`),o&&(o.textContent=d.valid?`${m}/${c} entries · cadena SHA3-256 intacta`:y?`rota en seq ${d.broken_at} · ${m}/${c} válidas`:d.error||"verificación fallida"),!d.valid&&d.error&&c===0&&(t.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${r(d.error)}</div>`),d.valid){if(b("done"),w().rewards){const v=document.getElementById("main-content");v==null||v.classList.add("reward-active"),setTimeout(()=>v==null?void 0:v.classList.remove("reward-active"),1400)}}else b("alert"),Y({icon:"⚠",message:y?`Violación de integridad en seq ${d.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`:`Verificación fallida: ${d.error||"error desconocido"}.`,actions:y?[{label:"Inspeccionar entrada",primary:!0,fn:()=>{T(),te(d.broken_at)}},{label:"Cerrar",fn:T}]:[{label:"Cerrar",primary:!0,fn:T}]});setTimeout(()=>b("idle"),3e3)}catch(d){clearInterval(p),t.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${r(d.message)}</div>`,b("idle")}e&&(e.disabled=!1,e.textContent="⚿ Verify Chain"),a&&setTimeout(()=>{a.style.display="none"},1500)}async function Xe(e){O("databases"),A({breadcrumb:k("BABYLON·60","Ontologies")}),e.innerHTML=`
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
  `;try{const t=await $("/api/databases");n.databaseList=t,U();const a=document.getElementById("db-table-body"),i=document.getElementById("db-total-count"),s=document.getElementById("db-total-size");if(i&&(i.textContent=t.length),s){const l=t.reduce((p,d)=>p+(d.size_bytes||0),0);s.textContent=l>1e6?`${(l/1e6).toFixed(1)} MB`:`${(l/1024).toFixed(0)} KB`}const o=l=>l.includes("ledger")?"LEDGER":l.includes("ontology")?"ONTOLOGY":l.includes("memory")||l.includes("cortex")?"CORTEX":l.includes("telemetry")?"TELEMETRY":l.includes("nexus")?"NEXUS":"GENERAL";a&&(a.innerHTML=t.map(l=>`
      <tr style="cursor:pointer" data-db="${r(l.name)}" title="Browse tables">
        <td class="stream-cell">${r(l.name)}</td>
        <td class="time-cell">${r(l.size_human||"—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${o(l.name)}</span></td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-db]").forEach(l=>{l.addEventListener("click",()=>Ze(l.dataset.db))})}catch(t){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${r(t.message)}</td></tr>`)}}async function Ze(e){const t=document.getElementById("db-tables-panel"),a=document.getElementById("db-tables-title"),i=document.getElementById("db-tables-body"),s=document.getElementById("db-browse-panel");if(!(!t||!i)){t.style.display="block",s&&(s.style.display="none"),a&&(a.textContent=`Tables — ${e}`),i.innerHTML='<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>',A({breadcrumb:k("BABYLON·60","Ontologies",e)});try{const o=await $(`/api/databases/${encodeURIComponent(e)}/tables`);if(o.length===0){i.innerHTML='<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>';return}i.innerHTML=o.map(l=>`
      <button class="btn" data-table="${r(l.name)}" style="font-size:0.62rem">
        ${r(l.name)} <span style="color:var(--gold);margin-left:4px">${l.row_count}</span>
      </button>
    `).join(""),i.querySelectorAll("[data-table]").forEach(l=>{l.addEventListener("click",()=>et(e,l.dataset.table))})}catch(o){i.innerHTML=`<span style="color:var(--break);font-size:0.68rem">${r(o.message)}</span>`}}}async function et(e,t){const a=document.getElementById("db-browse-panel"),i=document.getElementById("db-browse-title"),s=document.getElementById("db-browse-meta"),o=document.getElementById("db-schema-body"),l=document.getElementById("db-rows-body");if(!(!a||!l)){a.style.display="block",i&&(i.textContent=`${e} › ${t}`),o&&(o.textContent="Loading schema..."),l.innerHTML="",A({breadcrumb:k("BABYLON·60","Ontologies",e,t)});try{const[p,d]=await Promise.all([$(`/api/databases/${encodeURIComponent(e)}/schema/${encodeURIComponent(t)}`),$(`/api/databases/${encodeURIComponent(e)}/tables/${encodeURIComponent(t)}?limit=25`)]);o&&(o.innerHTML=p.map(c=>`<span style="margin-right:12px;white-space:nowrap">${c.pk?"⚿":"·"} ${r(c.name)} <span style="color:var(--dust-ghost)">${r(c.type||"")}</span></span>`).join("")),s&&(s.textContent=`${d.total} rows total · showing ${d.rows.length}`),d.rows.length===0?l.innerHTML='<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>':l.innerHTML=`
        <table class="data-table">
          <thead><tr>${d.columns.map(c=>`<th>${r(c)}</th>`).join("")}</tr></thead>
          <tbody>${d.rows.map(c=>`
            <tr>${d.columns.map(m=>{let u=c[m];u==null&&(u="—"),u=String(u);const y=u.length>90?u.slice(0,90)+"…":u;return`<td title="${r(u.slice(0,400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${r(y)}</td>`}).join("")}</tr>
          `).join("")}</tbody>
        </table>
      `}catch(p){l.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${r(p.message)}</div>`}}}async function tt(e){var a,i,s;O("query"),A({breadcrumb:k("BABYLON·60","SQL Console")}),n.databaseList.length===0&&await Ae(),e.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${n.databaseList.map(o=>`<option value="${r(o.name)}">${r(o.name)}</option>`).join("")}
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
  `;const t=async()=>{var m,u,y;const o=(u=(m=document.getElementById("query-input"))==null?void 0:m.value)==null?void 0:u.trim(),l=(y=document.getElementById("query-db-select"))==null?void 0:y.value;if(!o||!l)return;b("working");const p=document.getElementById("query-result-card"),d=document.getElementById("query-result-body"),c=document.getElementById("query-result-meta");p&&(p.style.display="block"),d&&(d.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const v=await G("/api/query",{database:l,sql:o}),f=v.rows||[],E=v.columns||[];c&&(c.textContent=`${v.row_count??f.length} rows · ${v.elapsed_ms??"—"}ms · ${v.database}`),d&&(f.length===0?d.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':d.innerHTML=`
            <table class="data-table">
              <thead><tr>${E.map(M=>`<th>${r(M)}</th>`).join("")}</tr></thead>
              <tbody>${f.map(M=>`<tr>${E.map(B=>{let L=M[B];L==null&&(L=""),L=String(L);const P=L.length>120?L.slice(0,120)+"…":L;return`<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${r(L.slice(0,400))}">${r(P)}</td>`}).join("")}</tr>`).join("")}</tbody>
            </table>
          `),b("done"),setTimeout(()=>b("idle"),2e3)}catch(v){d&&(d.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${r(v.message)}</div>`),b("idle")}};(a=document.getElementById("btn-run-query"))==null||a.addEventListener("click",t),(i=document.getElementById("btn-clear-query"))==null||i.addEventListener("click",()=>{const o=document.getElementById("query-input");o&&(o.value="");const l=document.getElementById("query-result-card");l&&(l.style.display="none")}),(s=document.getElementById("query-input"))==null||s.addEventListener("keydown",o=>{o.shiftKey&&o.key==="Enter"&&(o.preventDefault(),t())})}async function at(e){if(O("swarm"),A({breadcrumb:k("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'}),e.innerHTML=`
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
  `,nt(),n.telemetrySocket)try{n.telemetrySocket.close()}catch{}b("indexing"),n.telemetrySocket=ke("/ws/telemetry",t=>{n.telemetrySnapshot=t,st(t),n.tachometerState==="indexing"&&b("idle")},()=>{n.tachometerState==="indexing"&&b("idle")})}function nt(){var s;const e=document.getElementById("swarm-agents");if(!e)return;const t=n.lastVerify,a=n.sentinel,i=[{name:"MOSKV-1 APEX",status:"idle",task:"Meta-orquestador · esperando directiva",progress:0},{name:"BFT Verifier",status:t?t.valid?"done":"error":"idle",task:t?t.valid?`Cadena verificada: ${t.verified_entries}/${t.total_entries}`:`ROTA en seq ${t.broken_at}`:"Sin verificación en esta sesión",progress:t?100:0},{name:"Git Sentinel",status:a?(s=a.warnings)!=null&&s.some(o=>o.level==="red")?"error":"done":"idle",task:a?`${a.repo_name}@${a.branch??"—"} · ${a.dirty_files} dirty · delegación 100% al agente`:"Sin datos de repo",progress:a?100:0},{name:"Telemetry Stream",status:"running",task:"Empujando snapshots del sistema vía WS",progress:100}];e.innerHTML=i.map(o=>`
    <div class="agent-card">
      <div class="agent-card-header">
        <span class="agent-name">${o.name}</span>
        <span class="agent-status-pill ${o.status}">${o.status.toUpperCase()}</span>
      </div>
      <div class="agent-task">${r(o.task)}</div>
      <div class="agent-progress">
        <div class="agent-progress-fill ${o.status==="done"?"done":""}" style="width:${o.progress}%"></div>
      </div>
    </div>
  `).join("")}function st(e){var c,m,u,y;const t=document.getElementById("swarm-log-body");if(!t)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),i=((c=e.databases)==null?void 0:c.length)??0,s=e.total_db_size_mb!=null?`${e.total_db_size_mb}MB`:"—",o=((m=e.wal_files)==null?void 0:m.length)??0,l=((u=e.process)==null?void 0:u.max_rss_mb)!=null?`${e.process.max_rss_mb}MB`:"—",p=(y=e.git)!=null&&y.head?e.git.head.replace("ref: refs/heads/","@"):"",d=document.createElement("div");for(d.className="swarm-log-line",d.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${i} DBs · ${s} · WAL×${o} · RSS ${l} ${p?"· "+r(p):""}</span>
  `,t.appendChild(d);t.children.length>200;)t.removeChild(t.firstChild);t.scrollTop=t.scrollHeight,n.swarmLog.push({time:a,snap:e}),n.swarmLog.length>200&&n.swarmLog.shift()}async function it(e){var l,p,d;O("sentinel"),A({breadcrumb:k("BABYLON·60","Git Sentinel"),actions:'<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>'}),e.innerHTML='<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>';try{n.sentinel=await $("/api/sentinel/status")}catch(c){e.innerHTML=`<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${r(c.message)}</div></div>`;return}ie(),V();const t=n.sentinel,a=t.warnings.filter(c=>c.level==="red");t.warnings.filter(c=>c.level==="amber");const i=a.length===0,s=t.warnings.length===0?'<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>':t.warnings.map(c=>`
        <div class="sentinel-warning ${c.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${r(c.msg)}</span>
        </div>
      `).join(""),o=t.remotes.length===0?'<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>':t.remotes.map(c=>`<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${r(c.name)} → ${r(c.url)}</div>`).join("");e.innerHTML=`
    <div class="stats-grid slide-in">
      <div class="stat-card" style="border-left:2px solid ${i?"var(--verify)":"var(--break)"}">
        <div class="stat-label">Repo Actual (recalcado siempre — abajo en la barra de estado también)</div>
        <div class="stat-value ${i?"verify":"break"}" style="font-size:1rem">${r(t.repo_name)}</div>
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
        ${o}
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
  `,(l=document.getElementById("btn-sentinel-refresh"))==null||l.addEventListener("click",()=>Ie()),(p=document.getElementById("delegation-add"))==null||p.addEventListener("click",Le),(d=document.getElementById("delegation-input"))==null||d.addEventListener("keydown",c=>{c.key==="Enter"&&Le()}),de()}function Le(){const e=document.getElementById("delegation-input");!e||!e.value.trim()||(n.delegationQueue.unshift({id:Date.now(),text:e.value.trim(),state:"QUEUED",time:new Date().toISOString().slice(0,19)}),n.delegationQueue.length>30&&n.delegationQueue.pop(),localStorage.setItem("b60-delegation",JSON.stringify(n.delegationQueue)),e.value="",de(),w().rewards&&(b("done"),setTimeout(()=>b("idle"),1500)))}function de(){const e=document.getElementById("delegation-list");if(e){if(n.delegationQueue.length===0){e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>';return}e.innerHTML=n.delegationQueue.map(t=>`
    <div class="delegation-item">
      <span class="delegation-state">${t.state}</span>
      <span class="delegation-text">${r(t.text)}</span>
      <span class="delegation-time">${t.time.replace("T"," ")}</span>
      <span class="delegation-del" data-del="${t.id}" title="Retirar directiva">✕</span>
    </div>
  `).join(""),e.querySelectorAll("[data-del]").forEach(t=>{t.addEventListener("click",()=>{n.delegationQueue=n.delegationQueue.filter(a=>a.id!==parseInt(t.dataset.del)),localStorage.setItem("b60-delegation",JSON.stringify(n.delegationQueue)),de()})})}}async function lt(e){O("arena"),A({breadcrumb:k("BABYLON·60","Arena Matrix"),actions:'<span class="focus-badge live">ARENA MATRIX</span>'}),e.innerHTML=`
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
  `;try{const[t,a,i]=await Promise.all([$("/api/arena/leaderboard").catch(()=>({exists:!1,models:[]})),$("/api/arena/battles").catch(()=>({exists:!1,battles:[]})),$("/api/arena/conversations").catch(()=>({exists:!1,conversations:[]}))]),s=document.querySelector("#arena-leaderboard-table tbody"),o=document.getElementById("arena-leaderboard-meta");if(t.exists&&t.models.length>0){const d=t.meta;o.innerHTML=`
        <span>Latency: <b>${d.latency_ms}ms</b></span>
        <span>Entropy: <b>${d.entropy?d.entropy.toFixed(4):"—"}</b></span>
        <span>Updated: <b>${d.fetched_at?d.fetched_at.slice(11,19):"Recent"}</b></span>
      `,s.innerHTML=t.models.map(c=>{let m="rating-C",u="C",y="",v="Unknown";const f=c.model.toLowerCase();return f.includes("claude")||f.includes("qwen")||f.includes("llama")?(u="A",m="rating-A"):(f.includes("gemini")||f.includes("gpt"))&&(u="B",m="rating-B"),f.includes("claude")?(v="Moderate-High (RLHF)",y="risk-moderate"):f.includes("gpt")||f.includes("gemini")?(v="High (Strict refusal)",y="risk-high"):(f.includes("llama")||f.includes("qwen"))&&(v="Low-Moderate",y=""),`
          <tr>
            <td class="seq-cell" style="text-align:center;">#${c.rank}</td>
            <td class="stream-cell">${r(c.model)}</td>
            <td>${r(c.vendor)}</td>
            <td><b>${c.score}</b></td>
            <td>${c.votes}</td>
            <td><span class="exergy-badge ${m}">${u}</span></td>
            <td><span class="risk-tag ${y}">${v}</span></td>
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
      `).join(""),l.querySelectorAll(".battle-item").forEach(d=>{d.addEventListener("click",()=>{const c=parseInt(d.dataset.id),m=a.battles.find(u=>u.id===c);m&&ot(m)})})):l.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem;text-align:center;padding:24px;">No domestic battles recorded yet. Start arena_automata.py to run battles.</div>';const p=document.getElementById("arena-toxic-body");i.exists&&i.conversations.length>0?(p.innerHTML=`
        <div class="toxic-list">
          ${i.conversations.map((d,c)=>{const m=d.toxicity.toLowerCase()!=="none / none",u=m?"toxic-pill":"toxic-pill safe",y=m?"TOXIC/Jailbreak":"SAFE";return`
              <div class="toxic-item" data-idx="${c}">
                <div class="toxic-meta">
                  <span>ID: <b>${d.conv_id.slice(0,12)}...</b></span>
                  <span class="${u}">${y}</span>
                </div>
                <div class="chat-bubble">${r(d.prompt)}</div>
              </div>
            `}).join("")}
        </div>
      `,p.querySelectorAll(".toxic-item").forEach(d=>{d.addEventListener("click",()=>{const c=parseInt(d.dataset.idx),m=i.conversations[c];m&&dt(m)})})):p.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem;text-align:center;padding:24px;">Dataset conversations sample not found or empty.</div>'}catch(t){console.error(t)}}function ot(e){var i;const t=document.getElementById("entry-detail-panel");if(!t)return;t.classList.add("open"),t.setAttribute("aria-hidden","false");const a=(s,o,l="")=>`
    <div class="detail-field">
      <div class="detail-field-label">${s}</div>
      <div class="detail-field-value ${l}">${r(o??"—")}</div>
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
  `,(i=t.querySelector("#detail-close"))==null||i.addEventListener("click",R)}function dt(e){var i;const t=document.getElementById("entry-detail-panel");if(!t)return;t.classList.add("open"),t.setAttribute("aria-hidden","false");const a=(s,o,l="")=>`
    <div class="detail-field">
      <div class="detail-field-label">${s}</div>
      <div class="detail-field-value ${l}">${r(o??"—")}</div>
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
  `,(i=t.querySelector("#detail-close"))==null||i.addEventListener("click",R)}async function rt(e){var a;O("inference"),A({breadcrumb:k("BABYLON·60","Local Inference Console"),actions:'<span class="focus-badge live">LOCAL SILICON</span>'}),e.innerHTML=`
    <div class="arena-layout" style="grid-template-columns: 1.15fr 0.85fr; gap: 16px;">
      <!-- GENERATION CARD -->
      <div class="card slide-in" style="margin-bottom:0; display:flex; flex-direction:column; gap:12px; height:100%;">
        <div class="card-title">Sovereign Local Generation</div>
        
        <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
          <div style="flex:1; min-width:200px;">
            <label class="detail-field-label" for="inference-model-select">Target Silicon Model</label>
            <select class="select" id="inference-model-select" style="width:100%;">
              <option value="mamba">Native Mamba SSM (Integrated DAG Ledger)</option>
            </select>
          </div>
          
          <div style="width:100px;">
            <label class="detail-field-label" for="inference-max-tokens">Max Tokens</label>
            <input class="input" type="number" id="inference-max-tokens" value="30" min="5" max="100" style="width:100%; height:32px;">
          </div>
        </div>

        <div style="flex:1; display:flex; flex-direction:column; gap:6px;">
          <label class="detail-field-label" for="inference-prompt">Prompt Input</label>
          <textarea id="inference-prompt" placeholder="Type a prompt for local generation..." style="flex:1; min-height:100px; font-family:var(--body); padding:10px; background:rgba(0,0,0,0.3); border:1px solid var(--edge); border-radius:4px; color:var(--dust); resize:none;" spellcheck="false">Verification of local execution path</textarea>
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
            <div style="color:var(--dust-faint); text-align:center; padding:20px;">No generation trace logged. Run inference.</div>
          </div>
        </div>
      </div>
    </div>
  `;try{const i=await $("/api/inference/local/status"),s=document.getElementById("inference-model-select");s&&i&&i.status==="ONLINE"&&i.models&&i.models.forEach(o=>{const l=document.createElement("option");l.value=`ollama:${o}`,l.textContent=`${o} (Ollama daemon)`,s.appendChild(l)})}catch(i){console.error("Failed to load local models:",i)}const t=async()=>{var y,v,f;const i=document.getElementById("inference-model-select"),s=(v=(y=document.getElementById("inference-prompt"))==null?void 0:y.value)==null?void 0:v.trim(),o=parseInt(((f=document.getElementById("inference-max-tokens"))==null?void 0:f.value)||"30",10),l=document.getElementById("inference-output"),p=document.getElementById("inference-tps"),d=document.getElementById("inference-latency"),c=document.getElementById("inference-dag-body");if(!s||!i)return;b("working"),l&&(l.innerHTML='<span style="color:var(--dust-faint);">Inference ignited...</span>'),c&&(c.innerHTML='<div style="color:var(--dust-faint); text-align:center; padding:20px;">Computing state transitions...</div>');const m=i.value,u=performance.now();try{let E;if(m==="mamba")E=await G("/api/inference/local/mamba/generate",{prompt:s,max_tokens:o});else{const B=m.replace("ollama:","");E=await G("/api/inference/local/generate",{prompt:s,model:B,max_tokens:o})}const M=Math.round(performance.now()-u);l&&(l.textContent=E.text||"(empty response)"),p&&(p.textContent=`${E.tps??"—"} tps`),d&&(d.textContent=`${E.latency_ms??M} ms`),c&&(E.nodes&&E.nodes.length>0?c.innerHTML=`
            <div style="display:flex; flex-direction:column; gap:8px;">
              ${E.nodes.map((B,L)=>`
                <div style="border: 1px solid var(--edge); border-radius: 4px; padding: 6px; background: rgba(5,5,5,0.4);">
                  <div style="display:flex; justify-content:space-between; margin-bottom:4px;">
                    <span style="color:var(--gold); font-weight:700;">Node #${L}</span>
                    <span style="color:var(--verify); font-weight:700;">Verified</span>
                  </div>
                  <div style="color:var(--dust-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">ID: ${B.node_id.slice(0,16)}...</div>
                  <div style="color:var(--dust-dim); overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">Parent: ${B.parent_id.slice(0,16)}...</div>
                  <div style="margin-top:4px; font-weight:700; color:var(--dust); border-top:1px dashed var(--edge); padding-top:4px;">Claim: "${r(B.claim)}"</div>
                </div>
              `).join('<div style="text-align:center; color:var(--lapis-bright); font-size:0.8rem; margin:2px 0;">↓ parent link</div>')}
            </div>
          `:c.innerHTML=`
            <div style="color:var(--dust-faint); text-align:center; padding:20px;">
              No DAG trace returned for this model provider.
              <div style="font-size:0.55rem; margin-top:4px; color:var(--dust-ghost);">Only Native Mamba SSM records state transitions into the GraphLedger.</div>
            </div>
          `),b("done"),setTimeout(()=>b("idle"),2e3)}catch(E){l&&(l.innerHTML=`<span style="color:var(--break);">Error: ${r(E.message)}</span>`),c&&(c.innerHTML='<div style="color:var(--break); text-align:center; padding:20px;">Failed to verify state trace.</div>'),b("idle")}};(a=document.getElementById("btn-run-inference"))==null||a.addEventListener("click",t)}
