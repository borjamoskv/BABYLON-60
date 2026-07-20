(function(){const e=document.createElement("link").relList;if(e&&e.supports&&e.supports("modulepreload"))return;for(const s of document.querySelectorAll('link[rel="modulepreload"]'))n(s);new MutationObserver(s=>{for(const i of s)if(i.type==="childList")for(const o of i.addedNodes)o.tagName==="LINK"&&o.rel==="modulepreload"&&n(o)}).observe(document,{childList:!0,subtree:!0});function a(s){const i={};return s.integrity&&(i.integrity=s.integrity),s.referrerPolicy&&(i.referrerPolicy=s.referrerPolicy),s.crossOrigin==="use-credentials"?i.credentials="include":s.crossOrigin==="anonymous"?i.credentials="omit":i.credentials="same-origin",i}function n(s){if(s.ep)return;s.ep=!0;const i=a(s);fetch(s.href,i)}})();(function(){const t=new Lenis({duration:1.2,easing:f=>Math.min(1,1.001-Math.pow(2,-10*f)),direction:"vertical",gestureDirection:"vertical",smooth:!0,mouseMultiplier:1,smoothTouch:!1,touchMultiplier:2,infinite:!1});function e(f){t.raf(f),requestAnimationFrame(e)}requestAnimationFrame(e);const a=document.getElementById("cursor-magnet");let n=0,s=0,i=0,o=0;window.addEventListener("mousemove",f=>{n=f.clientX,s=f.clientY}),document.querySelectorAll("a, button, .btn").forEach(f=>{f.addEventListener("mouseenter",()=>a.classList.add("hover")),f.addEventListener("mouseleave",()=>a.classList.remove("hover"))});const r=document.getElementById("bg-canvas"),u=new THREE.Scene,c=new THREE.PerspectiveCamera(75,window.innerWidth/window.innerHeight,.1,1e3),p=new THREE.WebGLRenderer({canvas:r,alpha:!0,antialias:!0});p.setSize(window.innerWidth,window.innerHeight),p.setPixelRatio(Math.min(window.devicePixelRatio,2));const h=new THREE.BufferGeometry,v=3e3,g=new Float32Array(v*3),S=new Float32Array(v*3),T=new THREE.Color("#2B3BE5"),O=new THREE.Color("#F59E0B");for(let f=0;f<v*3;f+=3){const P=10+Math.random()*20,Y=Math.random()*Math.PI*2,j=Math.acos(Math.random()*2-1);g[f]=P*Math.sin(j)*Math.cos(Y),g[f+1]=P*Math.sin(j)*Math.sin(Y),g[f+2]=P*Math.cos(j)+(Math.random()*10-5);const V=T.clone().lerp(O,Math.random()*.4);S[f]=V.r,S[f+1]=V.g,S[f+2]=V.b}h.setAttribute("position",new THREE.BufferAttribute(g,3)),h.setAttribute("color",new THREE.BufferAttribute(S,3));const $=new THREE.PointsMaterial({size:.05,vertexColors:!0,blending:THREE.AdditiveBlending,transparent:!0,opacity:.8}),B=new THREE.Points(h,$);u.add(B),c.position.z=25;let w=new THREE.Clock;function k(){const f=w.getElapsedTime();i+=(n-i)*.2,o+=(s-o)*.2,a.style.transform=`translate(${i}px, ${o}px) translate(-50%, -50%)`,B.rotation.y=f*.05,B.rotation.x=f*.02,c.position.y=-(window.scrollY*.01),B.position.x=(n/window.innerWidth-.5)*2,B.position.y=-(s/window.innerHeight-.5)*2,p.render(u,c),requestAnimationFrame(k)}k(),window.addEventListener("resize",()=>{c.aspect=window.innerWidth/window.innerHeight,c.updateProjectionMatrix(),p.setSize(window.innerWidth,window.innerHeight)})})();const Ie="";async function I(t){const e=await fetch(`${Ie}${t}`);if(!e.ok){const a=await e.json().catch(()=>({detail:e.statusText}));throw new Error(a.detail||e.statusText)}return e.json()}async function z(t,e){const a=await fetch(`${Ie}${t}`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(e)});if(!a.ok){const n=await a.json().catch(()=>({detail:a.statusText}));throw new Error(n.detail||a.statusText)}return a.json()}function Me(t,e,a){const n=location.protocol==="https:"?"wss:":"ws:",s={closed:!1,ws:null},i=()=>{if(s.closed)return;const o=new WebSocket(`${n}//${location.host}${t}`);s.ws=o,o.onmessage=m=>{let r;try{r=JSON.parse(m.data)}catch{return}e(r)},o.onerror=m=>a==null?void 0:a(m),o.onclose=()=>{s.closed||setTimeout(i,3e3)}};return s.close=()=>{var o;s.closed=!0;try{(o=s.ws)==null||o.close()}catch{}},i(),s}const G={};let K=null;function R(t,e){G[t]=e}function x(t){if(K===t)return;K=t,document.querySelectorAll(".nav-item").forEach(a=>{a.classList.toggle("active",a.dataset.route===t)});const e=document.getElementById("main-content");G[t]&&(e.innerHTML="",G[t](e)),history.replaceState(null,"",`#${t}`)}function de(){const t=document.getElementById("main-content");K&&G[K]&&t&&(t.innerHTML="",G[K](t))}function Ce(){const t=location.hash.replace("#","");return t&&G[t]?t:"ledger"}const le={"2e":{key:"2e",label:"2E ◐",name:"Doble Excepcionalidad (TDAH + AACC)",tachometer:!0,loopGuard:!0,restoreBanner:!0,rewards:!0,spineLabels:!1},nt:{key:"nt",label:"NT ○",name:"Neurotípico",tachometer:!1,loopGuard:!1,restoreBanner:!1,rewards:!1,spineLabels:!0}};function L(){return le[l.cognitiveMode]||le["2e"]}function we(t){try{const e=JSON.parse(t||"[]");return Array.isArray(e)?e:[]}catch{return[]}}const l={cognitiveMode:localStorage.getItem("b60-cogmode")||"2e",contextPaneOpen:!0,bifocalMode:"micro",tachometerState:"idle",paletteOpen:!1,scratchpadOpen:!1,scratchpadItems:we(localStorage.getItem("b60-scratch")),delegationQueue:we(localStorage.getItem("b60-delegation")),databaseList:[],ledgerStats:null,lastVerify:null,sentinel:null,sentinelModalShown:!1,telemetrySnapshot:null,telemetrySocket:null,loopDetector:{route:null,routeEnteredAt:0,interventionFired:!1},sessionStart:Date.now(),activeRoute:null,swarmLog:[],canvasVB:{x:80,y:40,w:720,h:400},canvasAbort:null};document.addEventListener("DOMContentLoaded",async()=>{Be(l.cognitiveMode,{silent:!0}),b("indexing"),Se(),_e(),ze(),Ve(),Ue(),Ye(),Re(),Ae(),Ge(),await Promise.all([ke(),We(),qe()]),ue(),Q(),b("done"),L().restoreBanner&&Fe(localStorage.getItem("b60-route")||"ledger"),x(Ce()),b("idle")});function Be(t,{silent:e=!1}={}){l.cognitiveMode=le[t]?t:"2e",localStorage.setItem("b60-cogmode",l.cognitiveMode),document.body.classList.toggle("mode-2e",l.cognitiveMode==="2e"),document.body.classList.toggle("mode-nt",l.cognitiveMode==="nt");const a=document.getElementById("btn-cogmode");a&&(a.textContent=L().label,a.title=`Modo cognitivo: ${L().name} — click o ⌘⇧E para alternar`),e||(Se(),de(),ae({icon:L().key==="2e"?"◐":"○",message:`Modo cognitivo: ${L().name}. ${L().key==="2e"?"Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos.":"Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."}`}),setTimeout(A,3e3))}function ce(){Be(l.cognitiveMode==="2e"?"nt":"2e")}function Ae(){var e;let t=document.getElementById("btn-cogmode");if(!t){const a=(e=document.getElementById("btn-bifocal"))==null?void 0:e.parentElement;if(a){const n=document.createElement("div");n.className="status-segment",n.innerHTML='<button class="status-bifocal" id="btn-cogmode"></button>',a.parentElement.insertBefore(n,a),t=n.querySelector("#btn-cogmode")}}t&&(t.textContent=L().label,t.title=`Modo cognitivo: ${L().name} — click o ⌘⇧E para alternar`,t.addEventListener("click",ce))}function b(t){l.tachometerState=t;const e=document.getElementById("tachometer");e&&(e.className=`tachometer ${t!=="idle"?t:""}`);const a=document.getElementById("status-agent-segment");if(a)if(t==="working"||t==="indexing"){a.style.display="flex";const n=document.getElementById("status-agent-text");n&&(n.textContent=t==="indexing"?"Indexing context...":"Agent working...")}else a.style.display="none"}const He=[{id:"canvas",icon:"⬡",label:"Canvas",tip:"Architecture Canvas — ABSTRAER  ⌘5"},{id:"ledger",icon:"⧉",label:"Ledger",tip:"BFT Ledger — DETERMINAR  ⌘1"},{id:"databases",icon:"⛁",label:"Ontologies",tip:"Ontologies (explorador SQLite)  ⌘2"},{id:"query",icon:"❯_",label:"SQL",tip:"SQL Console (solo lectura)  ⌘3"},{id:"swarm",icon:"⚡",label:"Swarm",tip:"Agent Swarm (telemetría en vivo)  ⌘4"},{id:"analytics",icon:"∿",label:"Analytics",tip:"Ledger Analytics — DETERMINAR (agregación + BM25)  ⌘7"},{id:"sentinel",icon:"⎇",label:"Sentinel",tip:"Git Sentinel (identidad de repo + delegación real)  ⌘6"},{id:"inference",icon:"◈",label:"Inference",tip:"Local Inference (Ollama/MLX/Mamba)  ⌘8"}];function Se(){const t=document.getElementById("spine");if(!t)return;t.innerHTML="";const e=document.createElement("div");e.className="spine-logo",e.title="BABYLON·60 v1.1.0",e.innerHTML='<div class="spine-logo-dot"></div>',t.appendChild(e);const a=L().spineLabels;He.forEach((n,s)=>{if(s===1){const o=document.createElement("div");o.className="spine-separator",t.appendChild(o)}const i=document.createElement("button");i.className="spine-icon",i.dataset.route=n.id,a||(i.dataset.tooltip=n.tip),i.setAttribute("aria-label",n.tip),i.innerHTML=a?`<span class="spine-glyph">${n.icon}</span><span class="spine-label">${n.label}</span>`:n.icon,i.addEventListener("click",()=>x(n.id)),t.appendChild(i)}),Te(l.activeRoute)}function Te(t){document.querySelectorAll(".spine-icon").forEach(e=>{e.classList.toggle("active",e.dataset.route===t)})}function _e(){var t;(t=document.getElementById("btn-collapse-ctx"))==null||t.addEventListener("click",me),Q()}function me(){l.contextPaneOpen=!l.contextPaneOpen;const t=document.getElementById("context-pane"),e=document.getElementById("btn-collapse-ctx");t&&(t.classList.toggle("collapsed",!l.contextPaneOpen),e&&(e.textContent=l.contextPaneOpen?"⟨":"⟩"))}function Q(){var n,s,i,o,m;const t=document.getElementById("context-pane-body");if(!t)return;const e=l.databaseList.slice(0,5).map(r=>`
    <div class="ctx-item depth-1" data-goto-db="${d(r.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${d(r.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `).join(""),a=(s=(n=l.sentinel)==null?void 0:n.warnings)!=null&&s.some(r=>r.level==="red")?'<span class="ctx-item-badge break">!</span>':(o=(i=l.sentinel)==null?void 0:i.warnings)!=null&&o.length?'<span class="ctx-item-badge gold">△</span>':'<span class="ctx-item-badge verify">ok</span>';t.innerHTML=`
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
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${((m=l.ledgerStats)==null?void 0:m.entries)??"—"}</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">${l.databaseList.length||"—"}</span>
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
        ${l.scratchpadItems.length===0?'<span style="color:var(--dust-ghost)">No notes yet</span>':`<span style="color:var(--dust-dim)">${l.scratchpadItems.length} note${l.scratchpadItems.length>1?"s":""}</span>`}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Databases</div>
      ${e||'<div style="padding:4px 12px;font-size:0.62rem;color:var(--dust-ghost)">No .db discovered</div>'}
    </div>
  `,t.querySelectorAll(".ctx-item[data-route]").forEach(r=>{r.addEventListener("click",()=>x(r.dataset.route))}),t.querySelectorAll(".ctx-item[data-goto-db]").forEach(r=>{r.addEventListener("click",()=>x("databases"))})}function te(){var a;const t=document.getElementById("ctx-db-count");t&&(t.textContent=l.databaseList.length||"—");const e=document.getElementById("ctx-ledger-count");e&&(e.textContent=((a=l.ledgerStats)==null?void 0:a.entries)??"—")}function Oe(t){document.querySelectorAll(".ctx-item[data-route]").forEach(e=>{e.classList.toggle("active",e.dataset.route===t)})}function ue(){var o,m,r;const t=document.getElementById("status-conn-dot"),e=document.getElementById("status-conn-text"),a=document.getElementById("status-db-count"),n=document.getElementById("status-ledger-entries"),s=document.getElementById("status-lamport"),i=l.ledgerStats!==null||l.databaseList.length>0;t&&(t.className=i?"status-dot":"status-dot error"),e&&(e.textContent=i?"CONNECTED":"OFFLINE"),a&&(a.textContent=l.databaseList.length||"—"),n&&(n.textContent=((o=l.ledgerStats)==null?void 0:o.entries)??"—"),s&&(s.textContent=((r=(m=l.ledgerStats)==null?void 0:m.latest)==null?void 0:r.lamport_t)!=null?`L:${l.ledgerStats.latest.lamport_t}`:"—"),pe()}function pe(){var i,o;let t=document.getElementById("status-repo-segment");if(!t){const m=document.getElementById("status-bar"),r=m==null?void 0:m.querySelector(".status-segment");if(!m||!r)return;t=document.createElement("div"),t.className="status-segment",t.id="status-repo-segment",t.style.cursor="pointer",t.innerHTML='<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>',r.after(t),t.addEventListener("click",()=>x("sentinel"))}const e=document.getElementById("status-repo-text");if(!e)return;const a=l.sentinel;if(!a){e.textContent="—";return}const n=(i=a.warnings)==null?void 0:i.some(m=>m.level==="red"),s=!n&&((o=a.warnings)==null?void 0:o.length)>0;e.textContent=`${a.repo_name}${a.branch?" @"+a.branch:""}${a.head?" · "+a.head:""}${n?" ⚠":s?" △":" ✓"}`,e.style.color=n?"var(--break)":s?"var(--gold)":"var(--verify)",t.title=n?"LINAJE NO CANÓNICO — abre Git Sentinel":s?"Avisos de linaje — abre Git Sentinel":`Linaje canónico verificado (${a.commit_count??"—"} commits)`}async function qe(){var t;try{l.sentinel=await I("/api/sentinel/status"),pe();const e=((t=l.sentinel.warnings)==null?void 0:t.filter(a=>a.level==="red"))||[];e.length>0&&!l.sentinelModalShown&&(l.sentinelModalShown=!0,ae({icon:"⚠",message:`GIT SENTINEL: ${e[0].msg}`,actions:[{label:"Abrir Sentinel",primary:!0,fn:()=>{A(),x("sentinel")}},{label:"Entendido",fn:A}]}))}catch{}}function Re(){var t;(t=document.getElementById("btn-bifocal"))==null||t.addEventListener("click",ve)}function ve(){l.bifocalMode=l.bifocalMode==="micro"?"macro":"micro",document.body.classList.toggle("macro-mode",l.bifocalMode==="macro"),document.body.classList.toggle("micro-mode",l.bifocalMode==="micro");const t=document.getElementById("btn-bifocal");t&&(t.textContent=l.bifocalMode==="macro"?"MACRO ⊞":"MICRO ⊞"),l.bifocalMode==="macro"&&x("canvas")}const X=[{icon:"⬡",label:"Architecture Canvas",desc:"ABSTRAER: ver el sistema completo",shortcut:"⌘5",action:()=>x("canvas")},{icon:"⧉",label:"BFT Ledger",desc:"DETERMINAR: inspector de cadena de hashes",shortcut:"⌘1",action:()=>x("ledger")},{icon:"⛁",label:"Ontologies",desc:"Explorador SQLite (solo lectura)",shortcut:"⌘2",action:()=>x("databases")},{icon:"❯_",label:"SQL Console",desc:"Consultas read-only contra cualquier .db",shortcut:"⌘3",action:()=>x("query")},{icon:"⚡",label:"Agent Swarm",desc:"Telemetría en vivo (push WS, sin polling)",shortcut:"⌘4",action:()=>x("swarm")},{icon:"∿",label:"Ledger Analytics",desc:"DETERMINAR: agregación + búsqueda BM25 del ledger",shortcut:"⌘7",action:()=>x("analytics")},{icon:"⎇",label:"Git Sentinel",desc:"Identidad de repo + delegación real (commit/push)",shortcut:"⌘6",action:()=>x("sentinel")},{icon:"⌕",label:"Search Ledger",desc:"BM25 léxico sobre payloads y taints",shortcut:"",action:()=>{x("analytics"),setTimeout(()=>{var t;return(t=document.getElementById("ledger-search-input"))==null?void 0:t.focus()},300)}},{icon:"⚿",label:"Verify Chain Integrity",desc:"Recomputar SHA3-256 de toda la cadena",shortcut:"",action:()=>{x("ledger"),setTimeout(()=>{var t;return(t=document.getElementById("btn-verify-chain"))==null?void 0:t.click()},400)}},{icon:"◐",label:"Toggle Cognitive Mode",desc:"Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",shortcut:"⌘⇧E",action:ce},{icon:"⟨",label:"Toggle Context Pane",desc:"Mostrar / ocultar mapa semántico",shortcut:"⌘B",action:me},{icon:"⊞",label:"Toggle Macro / Micro",desc:"Alternar vista bifocal",shortcut:"⌘M",action:ve},{icon:"◎",label:"Open Scratchpad",desc:"Volcar un pensamiento sin perder foco",shortcut:"⌘⇧Space",action:()=>U(!0)}];let C=0,q=[...X];function ze(){const t=document.getElementById("palette-overlay"),e=document.getElementById("palette-input");!t||!e||(t.addEventListener("click",a=>{a.target===t&&F()}),e.addEventListener("input",()=>Ne(e.value)),e.addEventListener("keydown",je))}function De(){l.paletteOpen=!0;const t=document.getElementById("palette-overlay"),e=document.getElementById("palette-input");!t||!e||(t.classList.add("visible"),t.setAttribute("aria-hidden","false"),e.value="",C=0,q=[...X],J(),setTimeout(()=>e.focus(),50))}function F(){l.paletteOpen=!1;const t=document.getElementById("palette-overlay");t&&(t.classList.remove("visible"),t.setAttribute("aria-hidden","true"))}function Ne(t){const e=t.toLowerCase().trim();C=0,q=e?X.filter(a=>a.label.toLowerCase().includes(e)||a.desc.toLowerCase().includes(e)):[...X],J(e)}function Pe(t){return t.replace(/[.*+?^${}()|[\]\\]/g,"\\$&")}function J(t=""){const e=document.getElementById("palette-results");if(e){if(q.length===0){e.innerHTML=`<div class="palette-empty">No commands match "<strong>${d(t)}</strong>"</div>`;return}e.innerHTML=`
    <div class="palette-section-label">Commands</div>
    ${q.map((a,n)=>{const s=t?a.label.replace(new RegExp(`(${Pe(t)})`,"gi"),'<span class="palette-match">$1</span>'):a.label;return`
        <div class="palette-item ${n===C?"selected":""}" data-index="${n}">
          <span class="palette-item-icon">${a.icon}</span>
          <span class="palette-item-label">${s}</span>
          <span class="palette-item-desc">${a.desc}</span>
          ${a.shortcut?`<span class="palette-item-shortcut">${a.shortcut}</span>`:""}
        </div>
      `}).join("")}
  `,e.querySelectorAll(".palette-item").forEach(a=>{a.addEventListener("click",()=>{const n=parseInt(a.dataset.index);q[n]&&(q[n].action(),F())}),a.addEventListener("mouseenter",()=>{C=parseInt(a.dataset.index),e.querySelectorAll(".palette-item").forEach((n,s)=>n.classList.toggle("selected",s===C))})})}}function je(t){var e,a;if(t.key==="Escape"){F();return}t.key==="ArrowDown"&&(t.preventDefault(),C=Math.min(C+1,q.length-1),J(((e=document.getElementById("palette-input"))==null?void 0:e.value)||"")),t.key==="ArrowUp"&&(t.preventDefault(),C=Math.max(C-1,0),J(((a=document.getElementById("palette-input"))==null?void 0:a.value)||"")),t.key==="Enter"&&(t.preventDefault(),q[C]&&(q[C].action(),F()))}function Ve(){var a,n;const t=document.getElementById("scratchpad-modal"),e=document.getElementById("scratchpad-input");!t||!e||((a=document.getElementById("scratchpad-save"))==null||a.addEventListener("click",$e),(n=document.getElementById("scratchpad-close"))==null||n.addEventListener("click",()=>U(!1)),e.addEventListener("keydown",s=>{s.key==="Enter"&&!s.shiftKey&&(s.preventDefault(),$e()),s.key==="Escape"&&U(!1)}),ge())}function U(t){const e=document.getElementById("scratchpad-modal"),a=document.getElementById("scratchpad-input");e&&(l.scratchpadOpen=t!==void 0?t:!l.scratchpadOpen,e.classList.toggle("visible",l.scratchpadOpen),e.setAttribute("aria-hidden",String(!l.scratchpadOpen)),l.scratchpadOpen&&a&&setTimeout(()=>a.focus(),60))}function $e(){const t=document.getElementById("scratchpad-input");if(!t||!t.value.trim())return;const e={id:Date.now(),text:t.value.trim(),time:new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit"})};l.scratchpadItems.unshift(e),l.scratchpadItems.length>20&&l.scratchpadItems.pop(),localStorage.setItem("b60-scratch",JSON.stringify(l.scratchpadItems)),t.value="",ge(),Q(),L().rewards&&(b("done"),setTimeout(()=>b("idle"),2e3))}function ge(){const t=document.getElementById("scratchpad-items");if(t){if(l.scratchpadItems.length===0){t.innerHTML="";return}t.innerHTML=l.scratchpadItems.map(e=>`
    <div class="scratchpad-item" data-id="${e.id}">
      <span class="scratchpad-item-time">${e.time}</span>
      <span class="scratchpad-item-text">${d(e.text)}</span>
      <span class="scratchpad-item-del" data-del="${e.id}" title="Remove">✕</span>
    </div>
  `).join(""),t.querySelectorAll("[data-del]").forEach(e=>{e.addEventListener("click",a=>{a.stopPropagation();const n=parseInt(e.dataset.del);l.scratchpadItems=l.scratchpadItems.filter(s=>s.id!==n),localStorage.setItem("b60-scratch",JSON.stringify(l.scratchpadItems)),ge(),Q()})})}}function ae({icon:t="⬡",message:e,actions:a=[]}){const n=document.getElementById("agent-modal"),s=document.getElementById("agent-modal-icon"),i=document.getElementById("agent-modal-msg"),o=document.getElementById("agent-modal-actions");if(!n||!i||!o)return;s&&(s.textContent=t),i.textContent=e;const m=a.length>0?a:[{label:"Got it",fn:A,primary:!0}];o.innerHTML=m.map((r,u)=>`<button class="btn ${r.primary?"btn-primary":""}" style="font-size:0.65rem" data-action-idx="${u}">${r.label}</button>`).join(""),o.querySelectorAll("button").forEach(r=>{r.addEventListener("click",()=>{var u,c;return(c=(u=m[parseInt(r.dataset.actionIdx)])==null?void 0:u.fn)==null?void 0:c.call(u)})}),n.classList.add("visible"),n.setAttribute("aria-hidden","false"),L().tachometer&&b("alert")}function A(){const t=document.getElementById("agent-modal");t&&(t.classList.remove("visible"),t.setAttribute("aria-hidden","true")),b("idle")}function Ge(){setInterval(()=>{if(!L().loopGuard||!l.loopDetector.route||l.loopDetector.interventionFired)return;if(Date.now()-l.loopDetector.routeEnteredAt>1500*1e3){l.loopDetector.interventionFired=!0;const e=l.loopDetector.route;ae({icon:"⏱",message:`Llevas más de 25 minutos en ${e.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,actions:[{label:"Ver Arquitectura",primary:!0,fn:()=>{A(),x("canvas")}},{label:"Sigo aquí",fn:A},{label:"Volcar idea →",fn:()=>{A(),U(!0)}}]})}},120*1e3)}function Fe(t){var m;const e=document.getElementById("restore-banner"),a=document.getElementById("restore-msg"),n=document.getElementById("restore-points"),s=document.getElementById("restore-dismiss");if(!e||!a)return;const o=[`Last active: ${{ledger:"BFT Ledger",databases:"Ontologies",query:"SQL Console",swarm:"Agent Swarm",canvas:"Architecture Canvas",sentinel:"Git Sentinel"}[t]||t}`,`${l.databaseList.length||"—"} databases available`,((m=l.ledgerStats)==null?void 0:m.entries)!=null?`${l.ledgerStats.entries} ledger entries`:"Ledger loading...",l.sentinel?`repo ${l.sentinel.repo_name}@${l.sentinel.branch??"—"}`:""].filter(Boolean);a.textContent="Session restored · ",n&&(n.innerHTML=o.map(r=>`<span class="restore-point">${d(r)}</span>`).join("")),e.style.display="flex",s==null||s.addEventListener("click",()=>{e.style.display="none"}),setTimeout(()=>{e.style.display="none"},12e3)}function Ue(){const t={1:"ledger",2:"databases",3:"query",4:"swarm",5:"canvas",6:"sentinel",7:"analytics",8:"inference"};window.addEventListener("keydown",e=>{const a=e.metaKey||e.ctrlKey;if(a&&e.key==="k"&&!e.shiftKey){e.preventDefault(),l.paletteOpen?F():De();return}if(a&&e.shiftKey&&e.code==="Space"){e.preventDefault(),U();return}if(a&&e.shiftKey&&(e.key==="e"||e.key==="E")){e.preventDefault(),ce();return}if(a&&e.key==="b"&&!e.shiftKey){e.preventDefault(),me();return}if(a&&e.key==="m"&&!e.shiftKey){e.preventDefault(),ve();return}if(a&&t[e.key]){e.preventDefault(),x(t[e.key]);return}if(e.key==="Escape"){if(l.paletteOpen){F();return}if(l.scratchpadOpen){U(!1);return}ee()}})}function Ye(){R("canvas",Ke),R("ledger",Qe),R("databases",Je),R("query",tt),R("swarm",at),R("analytics",mt),R("sentinel",it),R("inference",pt),window.addEventListener("hashchange",()=>{const t=window.location.hash.replace("#","");t&&x(t)})}async function ke(){try{l.databaseList=await I("/api/databases"),te()}catch{}}async function We(){try{l.ledgerStats=await I("/api/ledger/stats"),te(),ue()}catch{}}function H({breadcrumb:t="",actions:e=""}={}){const a=document.getElementById("focus-breadcrumb"),n=document.getElementById("focus-actions");a&&(a.innerHTML=t),n&&(n.innerHTML=e)}function _(...t){return t.map((e,a)=>a<t.length-1?`<span class="breadcrumb-item">${e}</span><span class="breadcrumb-sep"> › </span>`:`<span class="breadcrumb-item current">${e}</span>`).join("")}function D(t){l.activeRoute=t,localStorage.setItem("b60-route",t),Te(t),Oe(t),ee(),t!=="swarm"&&l.telemetrySocket&&(l.telemetrySocket.close(),l.telemetrySocket=null),l.loopDetector.route!==t&&(l.loopDetector.route=t,l.loopDetector.routeEnteredAt=Date.now(),l.loopDetector.interventionFired=!1)}function d(t){return String(t??"").replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;")}async function Ke(t){var k,f,P,Y,j,V,ye;D("canvas"),H({breadcrumb:_("BABYLON·60","Architecture — ABSTRAER (ver el todo antes que la parte)"),actions:'<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>'});try{l.telemetrySnapshot=await I("/api/telemetry/snapshot")}catch{}const e=l.telemetrySnapshot,a=l.databaseList.length,n=((k=l.ledgerStats)==null?void 0:k.entries)??"—",s=(e==null?void 0:e.total_db_size_mb)!=null?`${e.total_db_size_mb}MB`:"—",i=l.sentinel,o=i!=null&&i.is_git?`${i.repo_name}@${i.branch??"—"} · ${i.head??"—"}`:"no git",m=(f=i==null?void 0:i.warnings)!=null&&f.some(y=>y.level==="red")?"err":(P=i==null?void 0:i.warnings)!=null&&P.length?"warn":"ok",r=[{id:"frontend",x:140,y:350,type:"FRONTEND",name:"BABYLON60 IDE",meta:`Vite · modo ${L().key.toUpperCase()}`,status:"ok"},{id:"fastapi",x:300,y:120,type:"BACKEND",name:"FastAPI",meta:"14 endpoints · ASGI",status:"ok"},{id:"ledger",x:620,y:80,type:"PERSISTENCE",name:"Master Ledger",meta:`${n} entries · SHA3-256 (huella criptográfica)`,status:(Y=l.ledgerStats)!=null&&Y.exists?"ok":"err",goto:"ledger"},{id:"ontology",x:620,y:220,type:"PERSISTENCE",name:"Ontology DBs",meta:`${a} DBs · ${s} · RO`,status:a>0?"ok":"warn",goto:"databases"},{id:"telemetry",x:620,y:350,type:"STREAM",name:"Telemetry Stream",meta:e?"WS push 2s (sin polling)":"offline",status:e?"ok":"warn",goto:"swarm"},{id:"git",x:140,y:240,type:"SENTINEL",name:"Git Sentinel",meta:o,status:m,goto:"sentinel"}],u=[{from:"frontend",to:"fastapi"},{from:"fastapi",to:"ledger"},{from:"fastapi",to:"ontology"},{from:"fastapi",to:"telemetry"},{from:"git",to:"fastapi"}],c={ok:"var(--verify)",warn:"var(--gold)",err:"var(--break)",idle:"var(--dust-ghost)"};t.innerHTML=`
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
  `;const p=document.getElementById("canvas-svg"),h=document.getElementById("canvas-edges"),v=document.getElementById("canvas-nodes");if(!p||!h||!v)return;u.forEach(({from:y,to:E})=>{const M=r.find(se=>se.id===y),W=r.find(se=>se.id===E);if(!M||!W)return;const fe=M.x+90,be=M.y+35,he=W.x,Ee=W.y+35,N=document.createElementNS("http://www.w3.org/2000/svg","path"),xe=(fe+he)/2;N.setAttribute("d",`M${fe},${be} C${xe},${be} ${xe},${Ee} ${he},${Ee}`),N.setAttribute("stroke","var(--edge)"),N.setAttribute("stroke-width","1.5"),N.setAttribute("fill","none"),N.setAttribute("opacity","0.5"),N.setAttribute("marker-end","url(#arrow)"),h.appendChild(N)}),r.forEach(y=>{const E=document.createElementNS("http://www.w3.org/2000/svg","foreignObject");E.setAttribute("x",y.x),E.setAttribute("y",y.y),E.setAttribute("width","195"),E.setAttribute("height","76");const M=document.createElement("div");M.className="canvas-node-card",M.style.position="relative",M.innerHTML=`
      <div class="canvas-node-type">${y.type}</div>
      <div class="canvas-node-name">${y.name}</div>
      <div class="canvas-node-meta">${d(y.meta)}</div>
      <div class="canvas-node-status" style="background:${c[y.status]||c.idle};box-shadow:0 0 5px ${c[y.status]||c.idle}"></div>
    `,y.goto&&M.addEventListener("click",()=>x(y.goto)),E.appendChild(M),v.appendChild(E)});const g=()=>p.setAttribute("viewBox",`${l.canvasVB.x} ${l.canvasVB.y} ${l.canvasVB.w} ${l.canvasVB.h}`),S=()=>{l.canvasVB={x:80,y:40,w:720,h:400},g()};S();const T=y=>{const E=l.canvasVB,M=E.x+E.w/2,W=E.y+E.h/2;E.w=Math.max(200,Math.min(2e3,E.w*y)),E.h=Math.max(110,Math.min(1100,E.h*y)),E.x=M-E.w/2,E.y=W-E.h/2,g()};(j=document.getElementById("canvas-zoom-in"))==null||j.addEventListener("click",()=>T(1/1.2)),(V=document.getElementById("canvas-zoom-out"))==null||V.addEventListener("click",()=>T(1.2)),(ye=document.getElementById("canvas-fit-btn"))==null||ye.addEventListener("click",S),p.addEventListener("wheel",y=>{y.preventDefault(),T(y.deltaY>0?1.1:1/1.1)},{passive:!1}),l.canvasAbort&&l.canvasAbort.abort(),l.canvasAbort=new AbortController;const O=l.canvasAbort.signal;let $=!1,B=0,w=0;p.addEventListener("pointerdown",y=>{$=!0,B=y.clientX,w=y.clientY}),window.addEventListener("pointermove",y=>{if(!$)return;const E=l.canvasVB.w/p.clientWidth;l.canvasVB.x-=(y.clientX-B)*E,l.canvasVB.y-=(y.clientY-w)*E,B=y.clientX,w=y.clientY,g()},{signal:O}),window.addEventListener("pointerup",()=>{$=!1},{signal:O})}let re=1;const ie=50;async function Qe(t){var e,a,n,s,i;D("ledger"),H({breadcrumb:_("BABYLON·60","BFT Ledger — DETERMINAR (verificar hasta el hash)"),actions:'<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>'}),(e=document.getElementById("btn-verify-chain"))==null||e.addEventListener("click",Xe),t.innerHTML=`
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
  `;try{const o=await I("/api/ledger/stats");l.ledgerStats=o;const m=document.getElementById("stat-db-name");m&&(m.textContent=o.db_path||"—");const r=document.getElementById("stat-total-entries");r&&(r.textContent=o.entries??0);const u=document.getElementById("stat-latest-lamport");u&&(u.textContent=`Lamport (reloj lógico causal): ${((a=o.latest)==null?void 0:a.lamport_t)??"—"}`);const c=document.getElementById("stat-latest-time");c&&((n=o.latest)!=null&&n.created_at)&&(c.textContent=String(o.latest.created_at).slice(0,19)),ue(),te()}catch{}await oe(1),(s=document.getElementById("btn-ledger-prev"))==null||s.addEventListener("click",()=>oe(re-1)),(i=document.getElementById("btn-ledger-next"))==null||i.addEventListener("click",()=>oe(re+1))}async function oe(t){t<1&&(t=1),re=t;const e=document.getElementById("ledger-table-body");if(e)try{const a=(t-1)*ie,n=await I(`/api/ledger/entries?limit=${ie}&offset=${a}`),s=n.entries||[],i=n.total??s.length;s.length===0?e.innerHTML='<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>':(e.innerHTML=s.map(c=>`
        <tr data-seq="${c.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${c.seq}</td>
          <td class="stream-cell">${d(c.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${d(c.entity_id)}</td>
          <td>${d(c.event_type)}</td>
          <td style="color:var(--dust-dim)">${c.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${d(c.cortex_taint)}">${d((c.cortex_taint||"—").slice(0,26))}${(c.cortex_taint||"").length>26?"…":""}</td>
          <td class="time-cell">${String(c.created_at||"").slice(0,19)}</td>
          <td class="hash-cell" title="${d(c.entry_hash)}">${(c.entry_hash||"—").slice(0,12)}…</td>
        </tr>
      `).join(""),e.querySelectorAll("tr[data-seq]").forEach(c=>{c.addEventListener("click",()=>Z(parseInt(c.dataset.seq)))}));const o=Math.max(1,Math.ceil(i/ie)),m=document.getElementById("ledger-page-info");m&&(m.textContent=`Page ${t} / ${o} · ${i} entries`);const r=document.getElementById("btn-ledger-prev"),u=document.getElementById("btn-ledger-next");r&&(r.disabled=t<=1),u&&(u.disabled=t>=o)}catch(a){e.innerHTML=`<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${d(a.message)}</td></tr>`}}async function Z(t){var a,n;const e=document.getElementById("entry-detail-panel");if(e){e.classList.add("open"),e.setAttribute("aria-hidden","false"),e.innerHTML=`<div class="detail-header"><span class="detail-title">⧉ Entry #${t}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`,(a=e.querySelector("#detail-close"))==null||a.addEventListener("click",ee);try{const s=await I(`/api/ledger/entry/${t}`);let i=s.payload_json||"";try{i=JSON.stringify(JSON.parse(s.payload_json),null,2)}catch{}const o=(m,r,u="")=>`
      <div class="detail-field">
        <div class="detail-field-label">${m}</div>
        <div class="detail-field-value ${u}">${d(r??"—")}</div>
      </div>`;e.innerHTML=`
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
    `,(n=e.querySelector("#detail-close"))==null||n.addEventListener("click",ee)}catch(s){const i=e.querySelector(".detail-body");i&&(i.innerHTML=`<span style="color:var(--break)">${d(s.message)}</span>`)}}}function ee(){const t=document.getElementById("entry-detail-panel");t&&(t.classList.remove("open"),t.setAttribute("aria-hidden","true"))}async function Xe(){const t=document.getElementById("btn-verify-chain"),e=document.getElementById("chain-visual-grid"),a=document.getElementById("verify-progress-wrap"),n=document.getElementById("verify-progress-bar"),s=document.getElementById("stat-integrity"),i=document.getElementById("verify-summary");if(!e)return;t&&(t.disabled=!0,t.textContent="⚙ Verifying..."),a&&(a.style.display="block"),b("working");let o=0;const m=setInterval(()=>{o=Math.min(o+8,90),n&&(n.style.width=`${o}%`)},120);try{const r=await z("/api/ledger/verify",{});l.lastVerify=r,clearInterval(m),n&&(n.style.width="100%");const u=r.total_entries??0,c=r.verified_entries??0,p=u-c;e.innerHTML="",(r.entries||[]).slice(0,400).forEach(v=>{const g=document.createElement("div");g.className=`chain-block ${v.valid?"":"invalid"}`,g.title=`Seq ${v.seq} · L:${v.lamport_t} · ${v.valid?"VALID":v.errors.join(" · ")}`,g.addEventListener("click",()=>Z(v.seq)),e.appendChild(g)}),u===0&&(e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>');const h=r.broken_at!=null;if(s&&(s.textContent=r.valid?"VERIFIED":h?`BROKEN (${p})`:"ERROR",s.className=`stat-value ${r.valid?"verify":"break"}`),i&&(i.textContent=r.valid?`${c}/${u} entries · cadena SHA3-256 intacta`:h?`rota en seq ${r.broken_at} · ${c}/${u} válidas`:r.error||"verificación fallida"),!r.valid&&r.error&&u===0&&(e.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(r.error)}</div>`),r.valid){if(b("done"),L().rewards){const v=document.getElementById("main-content");v==null||v.classList.add("reward-active"),setTimeout(()=>v==null?void 0:v.classList.remove("reward-active"),1400)}}else b("alert"),ae({icon:"⚠",message:h?`Violación de integridad en seq ${r.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`:`Verificación fallida: ${r.error||"error desconocido"}.`,actions:h?[{label:"Inspeccionar entrada",primary:!0,fn:()=>{A(),Z(r.broken_at)}},{label:"Cerrar",fn:A}]:[{label:"Cerrar",primary:!0,fn:A}]});setTimeout(()=>b("idle"),3e3)}catch(r){clearInterval(m),e.innerHTML=`<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${d(r.message)}</div>`,b("idle")}t&&(t.disabled=!1,t.textContent="⚿ Verify Chain"),a&&setTimeout(()=>{a.style.display="none"},1500)}async function Je(t){D("databases"),H({breadcrumb:_("BABYLON·60","Ontologies")}),t.innerHTML=`
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
  `;try{const e=await I("/api/databases");l.databaseList=e,te();const a=document.getElementById("db-table-body"),n=document.getElementById("db-total-count"),s=document.getElementById("db-total-size");if(n&&(n.textContent=e.length),s){const o=e.reduce((m,r)=>m+(r.size_bytes||0),0);s.textContent=o>1e6?`${(o/1e6).toFixed(1)} MB`:`${(o/1024).toFixed(0)} KB`}const i=o=>o.includes("ledger")?"LEDGER":o.includes("ontology")?"ONTOLOGY":o.includes("memory")||o.includes("cortex")?"CORTEX":o.includes("telemetry")?"TELEMETRY":o.includes("nexus")?"NEXUS":"GENERAL";a&&(a.innerHTML=e.map(o=>`
      <tr style="cursor:pointer" data-db="${d(o.name)}" title="Browse tables">
        <td class="stream-cell">${d(o.name)}</td>
        <td class="time-cell">${d(o.size_human||"—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${i(o.name)}</span></td>
      </tr>
    `).join("")),a==null||a.querySelectorAll("tr[data-db]").forEach(o=>{o.addEventListener("click",()=>Ze(o.dataset.db))})}catch(e){const a=document.getElementById("db-table-body");a&&(a.innerHTML=`<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${d(e.message)}</td></tr>`)}}async function Ze(t){const e=document.getElementById("db-tables-panel"),a=document.getElementById("db-tables-title"),n=document.getElementById("db-tables-body"),s=document.getElementById("db-browse-panel");if(!(!e||!n)){e.style.display="block",s&&(s.style.display="none"),a&&(a.textContent=`Tables — ${t}`),n.innerHTML='<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>',H({breadcrumb:_("BABYLON·60","Ontologies",t)});try{const i=await I(`/api/databases/${encodeURIComponent(t)}/tables`);if(i.length===0){n.innerHTML='<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>';return}n.innerHTML=i.map(o=>`
      <button class="btn" data-table="${d(o.name)}" style="font-size:0.62rem">
        ${d(o.name)} <span style="color:var(--gold);margin-left:4px">${o.row_count}</span>
      </button>
    `).join(""),n.querySelectorAll("[data-table]").forEach(o=>{o.addEventListener("click",()=>et(t,o.dataset.table))})}catch(i){n.innerHTML=`<span style="color:var(--break);font-size:0.68rem">${d(i.message)}</span>`}}}async function et(t,e){const a=document.getElementById("db-browse-panel"),n=document.getElementById("db-browse-title"),s=document.getElementById("db-browse-meta"),i=document.getElementById("db-schema-body"),o=document.getElementById("db-rows-body");if(!(!a||!o)){a.style.display="block",n&&(n.textContent=`${t} › ${e}`),i&&(i.textContent="Loading schema..."),o.innerHTML="",H({breadcrumb:_("BABYLON·60","Ontologies",t,e)});try{const[m,r]=await Promise.all([I(`/api/databases/${encodeURIComponent(t)}/schema/${encodeURIComponent(e)}`),I(`/api/databases/${encodeURIComponent(t)}/tables/${encodeURIComponent(e)}?limit=25`)]);i&&(i.innerHTML=m.map(u=>`<span style="margin-right:12px;white-space:nowrap">${u.pk?"⚿":"·"} ${d(u.name)} <span style="color:var(--dust-ghost)">${d(u.type||"")}</span></span>`).join("")),s&&(s.textContent=`${r.total} rows total · showing ${r.rows.length}`),r.rows.length===0?o.innerHTML='<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>':o.innerHTML=`
        <table class="data-table">
          <thead><tr>${r.columns.map(u=>`<th>${d(u)}</th>`).join("")}</tr></thead>
          <tbody>${r.rows.map(u=>`
            <tr>${r.columns.map(c=>{let p=u[c];p==null&&(p="—"),p=String(p);const h=p.length>90?p.slice(0,90)+"…":p;return`<td title="${d(p.slice(0,400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(h)}</td>`}).join("")}</tr>
          `).join("")}</tbody>
        </table>
      `}catch(m){o.innerHTML=`<div style="color:var(--break);font-size:0.7rem;padding:8px">${d(m.message)}</div>`}}}async function tt(t){var a,n,s;D("query"),H({breadcrumb:_("BABYLON·60","SQL Console")}),l.databaseList.length===0&&await ke(),t.innerHTML=`
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${l.databaseList.map(i=>`<option value="${d(i.name)}">${d(i.name)}</option>`).join("")}
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
  `;const e=async()=>{var c,p,h;const i=(p=(c=document.getElementById("query-input"))==null?void 0:c.value)==null?void 0:p.trim(),o=(h=document.getElementById("query-db-select"))==null?void 0:h.value;if(!i||!o)return;b("working");const m=document.getElementById("query-result-card"),r=document.getElementById("query-result-body"),u=document.getElementById("query-result-meta");m&&(m.style.display="block"),r&&(r.innerHTML='<div style="color:var(--dust-faint);padding:10px">Running...</div>');try{const v=await z("/api/query",{database:o,sql:i}),g=v.rows||[],S=v.columns||[];u&&(u.textContent=`${v.row_count??g.length} rows · ${v.elapsed_ms??"—"}ms · ${v.database}`),r&&(g.length===0?r.innerHTML='<div style="color:var(--dust-faint);padding:10px">No results</div>':r.innerHTML=`
            <table class="data-table">
              <thead><tr>${S.map(T=>`<th>${d(T)}</th>`).join("")}</tr></thead>
              <tbody>${g.map(T=>`<tr>${S.map(O=>{let $=T[O];$==null&&($=""),$=String($);const B=$.length>120?$.slice(0,120)+"…":$;return`<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d($.slice(0,400))}">${d(B)}</td>`}).join("")}</tr>`).join("")}</tbody>
            </table>
          `),b("done"),setTimeout(()=>b("idle"),2e3)}catch(v){r&&(r.innerHTML=`<div style="color:var(--break);padding:10px">Error: ${d(v.message)}</div>`),b("idle")}};(a=document.getElementById("btn-run-query"))==null||a.addEventListener("click",e),(n=document.getElementById("btn-clear-query"))==null||n.addEventListener("click",()=>{const i=document.getElementById("query-input");i&&(i.value="");const o=document.getElementById("query-result-card");o&&(o.style.display="none")}),(s=document.getElementById("query-input"))==null||s.addEventListener("keydown",i=>{i.shiftKey&&i.key==="Enter"&&(i.preventDefault(),e())})}async function at(t){if(D("swarm"),H({breadcrumb:_("BABYLON·60","Agent Swarm"),actions:'<span class="focus-badge live">LIVE</span>'}),t.innerHTML=`
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
  `,nt(),l.telemetrySocket)try{l.telemetrySocket.close()}catch{}b("indexing"),l.telemetrySocket=Me("/ws/telemetry",e=>{l.telemetrySnapshot=e,st(e),l.tachometerState==="indexing"&&b("idle")},()=>{l.tachometerState==="indexing"&&b("idle")})}function nt(){var s;const t=document.getElementById("swarm-agents");if(!t)return;const e=l.lastVerify,a=l.sentinel,n=[{name:"MOSKV-1 APEX",status:"idle",task:"Meta-orquestador · esperando directiva",progress:0},{name:"BFT Verifier",status:e?e.valid?"done":"error":"idle",task:e?e.valid?`Cadena verificada: ${e.verified_entries}/${e.total_entries}`:`ROTA en seq ${e.broken_at}`:"Sin verificación en esta sesión",progress:e?100:0},{name:"Git Sentinel",status:a?(s=a.warnings)!=null&&s.some(i=>i.level==="red")?"error":"done":"idle",task:a?`${a.repo_name}@${a.branch??"—"} · ${a.dirty_files} dirty · delegación 100% al agente`:"Sin datos de repo",progress:a?100:0},{name:"Telemetry Stream",status:"running",task:"Empujando snapshots del sistema vía WS",progress:100}];t.innerHTML=n.map(i=>`
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
  `).join("")}function st(t){var u,c,p,h;const e=document.getElementById("swarm-log-body");if(!e)return;const a=new Date().toLocaleTimeString("en-GB",{hour:"2-digit",minute:"2-digit",second:"2-digit"}),n=((u=t.databases)==null?void 0:u.length)??0,s=t.total_db_size_mb!=null?`${t.total_db_size_mb}MB`:"—",i=((c=t.wal_files)==null?void 0:c.length)??0,o=((p=t.process)==null?void 0:p.max_rss_mb)!=null?`${t.process.max_rss_mb}MB`:"—",m=(h=t.git)!=null&&h.head?t.git.head.replace("ref: refs/heads/","@"):"",r=document.createElement("div");for(r.className="swarm-log-line",r.innerHTML=`
    <span class="swarm-log-time">${a}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${n} DBs · ${s} · WAL×${i} · RSS ${o} ${m?"· "+d(m):""}</span>
  `,e.appendChild(r);e.children.length>200;)e.removeChild(e.firstChild);e.scrollTop=e.scrollHeight,l.swarmLog.push({time:a,snap:t}),l.swarmLog.length>200&&l.swarmLog.shift()}async function it(t){var o,m,r,u;D("sentinel"),H({breadcrumb:_("BABYLON·60","Git Sentinel"),actions:'<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>'}),t.innerHTML='<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>';try{l.sentinel=await I("/api/sentinel/status")}catch(c){t.innerHTML=`<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${d(c.message)}</div></div>`;return}pe(),Q();const e=l.sentinel,a=e.warnings.filter(c=>c.level==="red");e.warnings.filter(c=>c.level==="amber");const n=a.length===0,s=e.warnings.length===0?'<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>':e.warnings.map(c=>`
        <div class="sentinel-warning ${c.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${d(c.msg)}</span>
        </div>
      `).join(""),i=e.remotes.length===0?'<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>':e.remotes.map(c=>`<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${d(c.name)} → ${d(c.url)}</div>`).join("");t.innerHTML=`
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
        ${i}
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
  `,(o=document.getElementById("btn-sentinel-refresh"))==null||o.addEventListener("click",()=>de()),(m=document.getElementById("delegation-add"))==null||m.addEventListener("click",Le),(r=document.getElementById("delegation-input"))==null||r.addEventListener("keydown",c=>{c.key==="Enter"&&Le()}),(u=document.getElementById("btn-verify-ide-ledger"))==null||u.addEventListener("click",rt),await ne()}async function ne(){const t=document.getElementById("delegation-list");if(t)try{const e=await I("/api/delegation");ct(e.delegations||[])}catch(e){t.innerHTML=`<div style="color:var(--break);font-size:0.64rem">${d(e.message)}</div>`}}async function Le(){const t=document.getElementById("delegation-input"),e=document.getElementById("delegation-kind"),a=document.getElementById("delegation-status");if(!t||!t.value.trim())return;const n=t.value.trim(),s=(e==null?void 0:e.value)||"custom";try{const i=await z("/api/delegation",{directive:n,kind:s});t.value="",a&&(a.innerHTML=i.cloud_blocked?`<span style="color:var(--gold)">⛔ '${s}' encolado pero bloqueado por P0 — ejecútalo para ver el crash causal.</span>`:`<span style="color:var(--verify)">✓ '${s}' encolado (${i.delegation_id}).</span>`),L().rewards&&(b("done"),setTimeout(()=>b("idle"),1500)),await ne()}catch(i){a&&(a.innerHTML=`<span style="color:var(--break)">${d(i.message)}</span>`)}}async function ot(t){const e=document.getElementById("delegation-status");e&&(e.innerHTML=`<span style="color:var(--dust-faint)">Ejecutando ${t}…</span>`);try{const a=await z(`/api/delegation/${t}/execute`,{});if(e&&(e.innerHTML=`<span style="color:var(--verify)">✓ EXECUTED: ${d(a.result||"")}</span>`),L().rewards){const n=document.getElementById("main-content");n==null||n.classList.add("reward-active"),setTimeout(()=>n==null?void 0:n.classList.remove("reward-active"),1400)}}catch(a){e&&(e.innerHTML=`<span style="color:var(--break)">⛔ ${d(a.message)}</span>`),b("alert"),setTimeout(()=>b("idle"),2500)}await ne()}async function lt(t){try{await z(`/api/delegation/${t}/cancel`,{})}catch{}await ne()}async function rt(){const t=document.getElementById("delegation-status");try{const e=await z("/api/delegation/verify",{});t&&(t.innerHTML=e.valid?`<span style="color:var(--verify)">⚿ IDE CortexLedger íntegro: ${e.verified_entries}/${e.total_entries} eventos, cadena SHA-256 intacta.</span>`:`<span style="color:var(--break)">⚿ Cadena rota en seq ${e.broken_at} (${e.verified_entries}/${e.total_entries}).</span>`)}catch(e){t&&(t.innerHTML=`<span style="color:var(--break)">${d(e.message)}</span>`)}}const dt={QUEUED:"var(--gold)",EXECUTED:"var(--verify)",BLOCKED:"var(--break)",FAILED:"var(--break)",CANCELLED:"var(--dust-ghost)"};function ct(t){const e=document.getElementById("delegation-list");if(!e)return;if(!t||t.length===0){e.innerHTML='<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>';return}const a=new Set(["push","merge","ship","deploy"]);e.innerHTML=t.map(n=>{const s=n.state==="QUEUED",i=a.has(n.kind);return`
    <div class="delegation-item">
      <span class="delegation-state" style="color:${dt[n.state]||"var(--dust-dim)"};background:transparent;border:1px solid currentColor">${n.state}</span>
      <span class="delegation-kind-tag" title="${i?"op de nube — bloqueada por P0":"op local"}">${d(n.kind)}${i?" ⛔":""}</span>
      <span class="delegation-text">${d(n.directive)}${n.result?` <span style="color:var(--dust-faint)">— ${d(String(n.result).slice(0,80))}</span>`:""}</span>
      ${s?`<button class="btn delegation-exec" data-exec="${n.delegation_id}" style="font-size:0.56rem;padding:2px 7px">▶ EJECUTAR</button>`:""}
      ${s?`<span class="delegation-del" data-del="${n.delegation_id}" title="Cancelar">✕</span>`:""}
    </div>`}).join(""),e.querySelectorAll("[data-exec]").forEach(n=>n.addEventListener("click",()=>ot(n.dataset.exec))),e.querySelectorAll("[data-del]").forEach(n=>n.addEventListener("click",()=>lt(n.dataset.del)))}async function mt(t){var n,s,i;D("analytics"),H({breadcrumb:_("BABYLON·60","Ledger Analytics — DETERMINAR"),actions:'<button class="btn" id="btn-analytics-refresh" style="font-size:0.62rem">↺ Refresh</button>'}),t.innerHTML=`
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
  `,(n=document.getElementById("btn-analytics-refresh"))==null||n.addEventListener("click",()=>de());const e=()=>{var o;return ut(((o=document.getElementById("ledger-search-input"))==null?void 0:o.value)||"")};(s=document.getElementById("ledger-search-btn"))==null||s.addEventListener("click",e),(i=document.getElementById("ledger-search-input"))==null||i.addEventListener("keydown",o=>{o.key==="Enter"&&e()});const a=document.getElementById("analytics-body");try{const o=await I("/api/ledger/analytics"),m=(u,c,p,h)=>{const v=Math.max(...u.map(g=>g[p]),1);return u.map(g=>`
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span style="width:150px;font-size:0.64rem;color:var(--dust-dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${d(String(g[c]))}">${d(String(g[c]))}</span>
          <div style="flex:1;background:var(--tablet);border-radius:2px;height:14px;position:relative">
            <div style="width:${(g[p]/v*100).toFixed(1)}%;background:${h};height:100%;border-radius:2px;opacity:0.75"></div>
          </div>
          <span style="width:40px;text-align:right;font-size:0.62rem;color:var(--gold)">${g[p]}</span>
        </div>`).join("")},r=o.lamport;a.innerHTML=`
      <div class="stats-grid" style="margin-bottom:14px">
        <div class="stat-card"><div class="stat-label">Total Eventos</div><div class="stat-value gold">${o.total_entries}</div><div class="stat-sub">${d(o.db_path)}</div></div>
        <div class="stat-card"><div class="stat-label" title="Reloj lógico: sin huecos = orden causal total reconstruible">Continuidad Lamport</div><div class="stat-value ${r.contiguous?"verify":"break"}">${r.contiguous?"CONTIGUA":`${r.gaps} HUECOS`}</div><div class="stat-sub">L:${r.min}–${r.max} · ${r.distinct} distintos</div></div>
        <div class="stat-card"><div class="stat-label">Span Temporal</div><div class="stat-value lapis" style="font-size:0.8rem">${String(o.time_span.first||"—").slice(0,10)}</div><div class="stat-sub">→ ${String(o.time_span.last||"—").slice(0,10)}</div></div>
      </div>
      <div class="card" style="margin-bottom:12px"><div class="card-title" style="margin-bottom:8px">Streams</div>${m(o.streams,"stream","count","var(--lapis-bright)")}</div>
      <div class="card" style="margin-bottom:12px"><div class="card-title" style="margin-bottom:8px">Event Types</div>${m(o.event_types,"event_type","count","var(--verify)")}</div>
      <div class="card"><div class="card-title" style="margin-bottom:8px">Agentes <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(prefijo del causal_taint — quién escribió)</span></div>${m(o.agents,"agent","count","var(--gold)")}</div>
    `}catch(o){a.innerHTML=`<div class="empty-state" style="padding:24px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${d(o.message)}</div></div>`}}async function ut(t){const e=document.getElementById("ledger-search-results");if(e){if(!t.trim()){e.innerHTML="";return}e.innerHTML='<div style="color:var(--dust-faint);font-size:0.64rem">Rankeando…</div>';try{const a=await I(`/api/ledger/search?q=${encodeURIComponent(t)}&limit=15`);if(!a.results.length){e.innerHTML=`<div style="color:var(--dust-ghost);font-size:0.64rem">Sin coincidencias léxicas para «${d(t)}» en ${a.corpus_size} eventos.</div>`;return}e.innerHTML=`
      <div style="font-size:0.58rem;color:var(--dust-ghost);margin-bottom:6px">${a.results.length} resultados · ${d(a.method)} · corpus ${a.corpus_size}</div>
      ${a.results.map(n=>`
        <div class="search-hit" data-seq="${n.seq}" title="Abrir entrada #${n.seq}">
          <span class="search-score">${n.score.toFixed(2)}</span>
          <div style="flex:1;min-width:0">
            <div style="font-size:0.64rem;color:var(--dust-dim)"><b>#${n.seq}</b> · ${d(n.event_type)} · ${d(n.stream)}</div>
            <div style="font-size:0.58rem;color:var(--dust-faint);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${d(n.snippet)}</div>
          </div>
        </div>`).join("")}
    `,e.querySelectorAll("[data-seq]").forEach(n=>n.addEventListener("click",()=>Z(parseInt(n.dataset.seq))))}catch(a){e.innerHTML=`<div style="color:var(--break);font-size:0.64rem">${d(a.message)}</div>`}}}async function pt(t){var a,n;D("inference"),H({breadcrumb:_("BABYLON·60","Local Inference — SOVEREIGN SILICON"),actions:'<button class="btn" id="btn-infer-refresh" style="font-size:0.62rem">↺ Refresh Status</button>'}),t.innerHTML=`
    <div class="stats-grid" style="margin-bottom:14px">
      <div class="stat-card">
        <div class="stat-label">Local Daemon Status</div>
        <div class="stat-value break" id="infer-status-val">Probing...</div>
        <div class="stat-sub" id="infer-status-sub">Checking loopback...</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Model Provider</div>
        <div class="stat-value lapis" style="font-size:0.8rem">LOCAL SILICON</div>
        <div class="stat-sub">Zero-Network Confined</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Last Generation Metrics</div>
        <div class="stat-value gold" id="infer-speed-val">— tps</div>
        <div class="stat-sub" id="infer-latency-sub">— ms latency</div>
      </div>
    </div>

    <div class="card slide-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Local Generation Parameters</div>
      
      <div style="display:flex;gap:12px;margin-bottom:12px;flex-wrap:wrap">
        <div style="flex:1;min-width:200px">
          <label style="font-size:0.58rem;color:var(--dust-dim);display:block;margin-bottom:4px">Target Model</label>
          <select class="select" id="infer-model-select" style="width:100%">
            <option value="qwen2.5-coder:32b">qwen2.5-coder:32b (Ollama/MLX default)</option>
            <option value="native-mamba">Native Mamba SSM (Integrated GraphLedger)</option>
          </select>
        </div>
        <div style="width:120px">
          <label style="font-size:0.58rem;color:var(--dust-dim);display:block;margin-bottom:4px">Temperature</label>
          <input class="input" type="number" id="infer-temp-input" value="0.2" min="0.0" max="2.0" step="0.1" style="width:100%">
        </div>
        <div style="width:120px">
          <label style="font-size:0.58rem;color:var(--dust-dim);display:block;margin-bottom:4px">Max Tokens</label>
          <input class="input" type="number" id="infer-tokens-input" value="1024" min="1" max="8192" style="width:100%">
        </div>
      </div>

      <div class="code-editor" style="margin-bottom:12px">
        <textarea id="infer-prompt-input" placeholder="Type prompt here... (e.g. Write a brief explanation of BFT consensus in 2 sentences)" spellcheck="false" style="height:120px"></textarea>
      </div>

      <div style="display:flex;justify-content:space-between;align-items:center">
        <span style="font-size:0.58rem;color:var(--dust-ghost)">Confined to loopback (127.0.0.1 / localhost)</span>
        <button class="btn btn-primary" id="btn-run-inference">⚡ Generate Output</button>
      </div>
    </div>

    <div id="infer-output-card" class="card fade-in" style="display:none;margin-bottom:14px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title">Output Integrity</div>
        <span id="infer-output-hash" style="font-family:var(--mono);font-size:0.58rem;color:var(--gold)"></span>
      </div>
      <pre id="infer-output-body" style="font-family:var(--mono);font-size:0.68rem;background:var(--bitumen);padding:14px;border:1px solid var(--edge);border-radius:2px;white-space:pre-wrap;margin:0;max-height:400px;overflow-y:auto;color:var(--dust)"></pre>
    </div>

    <div id="mamba-trace-card" class="card fade-in" style="display:none">
      <div class="card-title" style="margin-bottom:10px">Mamba GraphLedger Trace</div>
      <div id="mamba-trace-body"></div>
    </div>
  `;const e=async()=>{const s=document.getElementById("infer-status-val"),i=document.getElementById("infer-status-sub"),o=document.getElementById("infer-model-select");if(!(!s||!i||!o))try{const m=await I("/api/inference/local/status");if(m.status==="ONLINE"){s.textContent="ONLINE",s.className="stat-value verify",i.textContent=`Running at ${m.endpoint}`;const r=o.value;o.innerHTML=`<option value="native-mamba" ${r==="native-mamba"?"selected":""}>Native Mamba SSM (Integrated GraphLedger)</option>`,(m.models||[]).forEach(u=>{o.innerHTML+=`<option value="${d(u)}" ${r===u?"selected":""}>${d(u)}</option>`})}else s.textContent="OFFLINE",s.className="stat-value break",i.textContent=`Daemon offline at ${m.endpoint}`}catch(m){s.textContent="ERROR",s.className="stat-value break",i.textContent=m.message}};(a=document.getElementById("btn-infer-refresh"))==null||a.addEventListener("click",e),await e(),(n=document.getElementById("btn-run-inference"))==null||n.addEventListener("click",async()=>{var S,T,O,$,B;const s=(T=(S=document.getElementById("infer-prompt-input"))==null?void 0:S.value)==null?void 0:T.trim(),i=(O=document.getElementById("infer-model-select"))==null?void 0:O.value,o=parseFloat((($=document.getElementById("infer-temp-input"))==null?void 0:$.value)||"0.2"),m=parseInt(((B=document.getElementById("infer-tokens-input"))==null?void 0:B.value)||"1024");if(!s)return;b("working");const r=document.getElementById("infer-output-card"),u=document.getElementById("infer-output-body"),c=document.getElementById("infer-output-hash"),p=document.getElementById("mamba-trace-card"),h=document.getElementById("mamba-trace-body"),v=document.getElementById("infer-speed-val"),g=document.getElementById("infer-latency-sub");r&&(r.style.display="block"),u&&(u.textContent="Generating..."),c&&(c.textContent=""),p&&(p.style.display="none");try{if(i==="native-mamba"){const w=await z("/api/inference/local/mamba/generate",{prompt:s,max_tokens:Math.min(m,100)});u&&(u.textContent=w.text),c&&(c.textContent=`Provider: ${w.provider} · Vocab: ${w.vocab_size}`),v&&(v.textContent="N/A"),g&&(g.textContent="Instant generation"),p&&h&&w.nodes&&w.nodes.length>0&&(p.style.display="block",h.innerHTML=`
            <div style="display:flex;flex-direction:column;gap:8px;margin-top:10px">
              ${w.nodes.map((k,f)=>`
                <div style="border-left:2px solid var(--gold);padding-left:12px;margin-bottom:6px">
                  <div style="font-size:0.64rem;color:var(--dust-dim)">
                    <b>Node #${f+1}: ${d(k.node_id.slice(0,12))}</b> 
                    ${k.parent_id?`(Parent: ${d(k.parent_id.slice(0,12))})`:"(Root)"}
                  </div>
                  <div style="font-size:0.6rem;color:var(--gold);font-family:var(--mono);margin:2px 0">${d(k.claim)}</div>
                  <div style="font-size:0.54rem;color:var(--dust-ghost);font-family:var(--mono)">payload_hash: ${k.payload_hash}</div>
                </div>
              `).join("")}
            </div>
          `)}else{const w=await z("/api/inference/local/generate",{prompt:s,model:i,temperature:o,max_tokens:m});u&&(u.textContent=w.text),c&&(c.textContent=`SHA256: ${w.sha256.slice(0,32)}...`),v&&(v.textContent=`${w.tps} tps`),g&&(g.textContent=`${w.latency_ms} ms latency`)}}catch(w){u&&(u.textContent=`Error: ${w.message}`)}finally{b("idle")}})}
