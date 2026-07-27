class h{constructor(){this.cache=null,this.cacheExpiry=0,this.CACHE_DURATION=5*60*1e3}async getExposiciones(){if(this.cache&&Date.now()<this.cacheExpiry)return this.cache;let t=null;try{if(t=await this.fetchFromNotebookLM(),t&&t.length>0)return this.setCache(t),t}catch(e){Logger.warn("[ExposicionesData] NotebookLM unavailable:",e.message)}try{return t=await this.fetchFromLocalJSON(),this.setCache(t),t}catch(e){return Logger.error("[ExposicionesData] Local JSON failed:",e),[]}}async fetchFromNotebookLM(){var n,r,o,c,l;if(!window.micaInstance||!window.micaInstance.apiKey)throw new Error("MICA/Gemini not configured");const e=await fetch("https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key="+window.micaInstance.apiKey,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({contents:[{parts:[{text:`
            Eres el asistente de Naroa Gutiérrez Gil. 
            Dame un JSON array con TODAS las exposiciones de Naroa desde 2013 hasta 2025.
            Formato exacto por exposición:
            {
                "id": "kebab-case-id",
                "title": "Título",
                "subtitle": "Subtítulo opcional",
                "location": "Lugar, Ciudad",
                "year": 2024,
                "month": "January",
                "day": 15,
                "type": "solo|group|online|market|festival|publication",
                "description": "Descripción opcional",
                "url": "URL opcional"
            }
            Responde SOLO con el JSON array, sin explicaciones.
        `}]}],generationConfig:{temperature:.1,maxOutputTokens:8e3}})});if(!e.ok)throw new Error(`Gemini API error: ${e.status}`);const s=(((l=(c=(o=(r=(n=(await e.json()).candidates)==null?void 0:n[0])==null?void 0:r.content)==null?void 0:o.parts)==null?void 0:c[0])==null?void 0:l.text)||"").match(/\[[\s\S]*\]/);if(!s)throw new Error("No JSON array found in response");return JSON.parse(s[0])}async fetchFromLocalJSON(){const t=await fetch("/data/exhibitions.json");if(!t.ok)throw new Error(`HTTP ${t.status}`);return(await t.json()).exhibitions||[]}setCache(t){this.cache=t,this.cacheExpiry=Date.now()+this.CACHE_DURATION}invalidateCache(){this.cache=null,this.cacheExpiry=0}groupByYear(t){const e={};return t.forEach(a=>{const i=a.year;e[i]||(e[i]=[]),e[i].push(a)}),e}filterByType(t,e){return t.filter(a=>a.type===e)}getStats(t){const e={};t.forEach(i=>{e[i.type]=(e[i.type]||0)+1});const a=[...new Set(t.map(i=>i.year))].sort();return{total:t.length,byType:e,yearRange:a.length?`${a[0]}-${a[a.length-1]}`:"N/A",soloCount:e.solo||0,groupCount:e.group||0}}}const p=new h;class u{constructor(){this.container=null,this.data=[],this.filteredData=null,this.activeYear=null,this.activeFilter="all",this.dataService=p,this.mousePos={x:0,y:0},this.particles=[],this.raf=null}async init(t="exposiciones-container"){if(this.container=document.getElementById(t),!this.container){Logger.error("[ExposicionesTimeline] Container not found");return}this.container.textContent="";const e=document.createElement("div");e.className="timeline-loading",e.textContent="",e.insertAdjacentHTML("afterbegin",`
                <div class="loading-shimmer"></div>
                <span class="loading-text">Cargando trayectoria...</span>
        `),this.container.appendChild(e),await this.loadData(),this.render(),this.attachEvents(),this.initWowEffects(),this.dataService.getStats(this.data)}async loadData(){try{this.data=await this.dataService.getExposiciones(),this.data.sort((t,e)=>e.year-t.year)}catch(t){Logger.error("Failed to load exhibitions:",t),this.data=[]}}groupByYear(){const t=this.filteredData||this.data,e={};return t.forEach(a=>{const i=a.year;e[i]||(e[i]=[]),e[i].push(a)}),e}getTypeIcon(t){return{solo:"🎨",group:"👥",online:"🌐",market:"🛒",festival:"🎪",publication:"📰"}[t]||"📍"}getTypeBadgeClass(t){return{solo:"badge-solo",group:"badge-group",online:"badge-online",market:"badge-market",festival:"badge-festival",publication:"badge-publication"}[t]||"badge-default"}render(){var i;const t=this.groupByYear(),e=Object.keys(t).sort((s,n)=>n-s),a=this.data.length;this.container.innerHTML=`
            <section class="exposiciones-timeline">
                <!-- Canvas para partículas -->
                <canvas class="particles-canvas" id="timeline-particles"></canvas>
                
                <!-- Header con Kinetic Typography -->
                <header class="timeline-header">
                    <h1 class="timeline-title kinetic-text">
                        <span class="title-number" data-value="${a}">0</span>
                        <span class="title-word">Exposiciones</span>
                    </h1>
                    <p class="timeline-subtitle reveal-text">
                        <span>2013</span>
                        <span class="subtitle-line"></span>
                        <span>2026</span>
                    </p>
                    <div class="subtitle-glow"></div>
                </header>

                <!-- Filtros por tipo -->
                <div class="timeline-filters">
                    <button class="filter-btn active" data-filter="all">Todas</button>
                    <button class="filter-btn" data-filter="solo">🎨 Individual</button>
                    <button class="filter-btn" data-filter="group">👥 Colectiva</button>
                    <button class="filter-btn" data-filter="market">🛒 Market</button>
                    <button class="filter-btn" data-filter="festival">🎪 Festival</button>
                    <button class="filter-btn" data-filter="online">🌐 Online</button>
                    <button class="filter-btn" data-filter="publication">📰 Publicación</button>
                </div>

                <!-- Navegación con efecto magnético -->
                <nav class="timeline-nav magnetic-nav">
                    <div class="nav-backdrop"></div>
                    ${e.map((s,n)=>`
                        <button class="year-btn magnetic-btn ${n===0?"active":""}" 
                                data-year="${s}"
                                style="--delay: ${n*.05}s">
                            <span class="btn-text">${s}</span>
                            <span class="btn-glow"></span>
                        </button>
                    `).join("")}
                </nav>

                <!-- Timeline Track con línea animada -->
                <div class="timeline-track">
                    <div class="timeline-line">
                        <div class="line-progress"></div>
                        <div class="line-pulse"></div>
                    </div>
                    
                    ${e.map((s,n)=>`
                        <div class="timeline-year-group" data-year="${s}" style="--group-delay: ${n*.1}s">
                            <div class="year-marker">
                                <div class="marker-orb">
                                    <div class="orb-ring"></div>
                                    <div class="orb-core"></div>
                                </div>
                                <span class="year-label">${s}</span>
                                <span class="year-count">${t[s].length} ${t[s].length===1?"expo":"expos"}</span>
                            </div>
                            
                            <div class="exhibitions-grid">
                                ${t[s].map((r,o)=>this.renderCard(r,o)).join("")}
                            </div>
                        </div>
                    `).join("")}
                </div>

                <!-- Stats Footer Flotante -->
                <footer class="timeline-footer">
                    <div class="stat-chip"><span class="stat-value">${a}</span> Total</div>
                    <div class="stat-chip"><span class="stat-value">${e.length}</span> Años</div>
                    <div class="stat-chip"><span class="stat-value">${((i=t[e[0]])==null?void 0:i.length)||0}</span> Este año</div>
                </footer>
            </section>
        `}renderCard(t,e){const a=t.month?`${t.month}${t.day?` ${t.day}`:""}`:"",i=t.image&&t.image.length>0;return`
            <article class="expo-card tilt-card ${i?"has-image":""}" 
                     data-id="${t.id}" 
                     style="--card-delay: ${e*.08}s">
                <div class="card-shine"></div>
                <div class="card-glow"></div>
                
                ${i?`
                    <div class="card-image">
                        <img src="${t.image}" 
                             alt="${t.title}"
                             loading="lazy"
                             decoding="async"
                             onerror="this.parentElement.classList.add('img-error')">
                        <div class="image-overlay"></div>
                    </div>
                `:""}
                
                <div class="card-content">
                    <div class="card-header">
                        <span class="expo-icon">${this.getTypeIcon(t.type)}</span>
                        <span class="expo-badge ${this.getTypeBadgeClass(t.type)}">
                            ${t.type.toUpperCase()}
                        </span>
                    </div>
                    
                    <h3 class="expo-title">${t.title}</h3>
                    ${t.subtitle?`<p class="expo-subtitle">${t.subtitle}</p>`:""}
                    
                    <div class="expo-meta">
                        <span class="expo-location">
                            <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/>
                                <circle cx="12" cy="10" r="3"/>
                            </svg>
                            ${t.location}
                        </span>
                        ${a?`<span class="expo-date">📅 ${a}</span>`:""}
                    </div>

                    ${t.description?`
                        <p class="expo-description">${t.description}</p>
                    `:""}

                    ${t.url?`
                        <a href="${t.url}" target="_blank" rel="noopener" class="expo-link magnetic-btn">
                            <span>Ver más</span>
                            <svg class="arrow-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
                                <path d="M5 12h14M12 5l7 7-7 7"/>
                            </svg>
                        </a>
                    `:""}
                </div>
            </article>
        `}attachEvents(){this.container.querySelectorAll(".year-btn").forEach(t=>{t.addEventListener("click",e=>{this.scrollToYear(e.currentTarget.dataset.year),this.updateActiveYear(e.currentTarget)})}),this.container.querySelectorAll(".filter-btn").forEach(t=>{t.addEventListener("click",e=>{const a=e.currentTarget.dataset.filter;this.activeFilter=a,this.container.querySelectorAll(".filter-btn").forEach(i=>i.classList.remove("active")),e.currentTarget.classList.add("active"),this.filteredData=a==="all"?null:this.data.filter(i=>i.type===a),this.render(),this.attachEvents(),this.initWowEffects()})}),this.container.addEventListener("mousemove",t=>{this.mousePos={x:t.clientX,y:t.clientY}}),this.container.querySelectorAll(".tilt-card").forEach(t=>{t.addEventListener("mousemove",e=>this.handleTilt(t,e)),t.addEventListener("mouseleave",()=>this.resetTilt(t)),t.addEventListener("mouseenter",()=>this.activateCard(t))}),this.setupScrollAnimations(),this.setupScrollProgress()}initWowEffects(){this.animateCountUp()}animateCountUp(){const t=this.container.querySelector(".title-number");if(!t)return;const e=parseInt(t.dataset.value);let a=0;const s=e/(2e3/16),n=()=>{a+=s,a<e?(t.textContent=Math.floor(a),requestAnimationFrame(n)):t.textContent=e};setTimeout(n,300)}initParticleCanvas(){const t=this.container.querySelector("#timeline-particles");if(t){t.width=window.innerWidth,t.height=window.innerHeight,this.ctx=t.getContext("2d");for(let e=0;e<50;e++)this.particles.push({x:Math.random()*t.width,y:Math.random()*t.height,size:Math.random()*2+.5,speedX:(Math.random()-.5)*.5,speedY:(Math.random()-.5)*.5,opacity:Math.random()*.5+.1})}}startParticleLoop(){if(!this.ctx)return;const t=()=>{this.ctx.clearRect(0,0,this.ctx.canvas.width,this.ctx.canvas.height),this.particles.forEach(e=>{e.x+=e.speedX,e.y+=e.speedY,e.x<0&&(e.x=this.ctx.canvas.width),e.x>this.ctx.canvas.width&&(e.x=0),e.y<0&&(e.y=this.ctx.canvas.height),e.y>this.ctx.canvas.height&&(e.y=0),this.ctx.beginPath(),this.ctx.arc(e.x,e.y,e.size,0,Math.PI*2),this.ctx.fillStyle=`rgba(50, 205, 50, ${e.opacity})`,this.ctx.fill()}),this.raf=requestAnimationFrame(t)};t()}handleTilt(t,e){const a=t.getBoundingClientRect(),i=(e.clientX-a.left)/a.width-.5,s=(e.clientY-a.top)/a.height-.5;t.style.transform=`
            perspective(1000px)
            rotateY(${i*15}deg)
            rotateX(${s*-15}deg)
            scale3d(1.02, 1.02, 1.02)
        `;const n=t.querySelector(".card-shine");n&&(n.style.background=`radial-gradient(
                circle at ${e.clientX-a.left}px ${e.clientY-a.top}px,
                rgba(50, 205, 50, 0.15) 0%,
                transparent 50%
            )`)}resetTilt(t){t.style.transform="perspective(1000px) rotateY(0) rotateX(0) scale3d(1, 1, 1)";const e=t.querySelector(".card-shine");e&&(e.style.background="transparent")}activateCard(t){const e=t.querySelector(".card-glow");e&&(e.style.opacity="1")}updateActiveYear(t){this.container.querySelectorAll(".year-btn").forEach(e=>e.classList.remove("active")),t.classList.add("active")}scrollToYear(t){const e=this.container.querySelector(`[data-year="${t}"]`);e&&e.scrollIntoView({behavior:"smooth",block:"start"})}setupScrollAnimations(){const t=new IntersectionObserver(e=>{e.forEach(a=>{a.isIntersecting&&(a.target.classList.add("visible"),a.target.style.animationDelay=a.target.style.getPropertyValue("--card-delay"))})},{threshold:.1,rootMargin:"0px 0px -50px 0px"});this.container.querySelectorAll(".expo-card, .timeline-year-group").forEach(e=>{t.observe(e)})}setupScrollProgress(){const t=this.container.querySelector(".line-progress");t&&window.addEventListener("scroll",()=>{const e=this.container.querySelector(".timeline-track");if(!e)return;const a=e.getBoundingClientRect(),i=Math.min(1,Math.max(0,(window.innerHeight-a.top)/(a.height+window.innerHeight)));t.style.height=`${i*100}%`},{passive:!0})}destroy(){this.raf&&cancelAnimationFrame(this.raf),this.particles=[]}}const g=new u;export{g as default,g as exposicionesTimeline};
