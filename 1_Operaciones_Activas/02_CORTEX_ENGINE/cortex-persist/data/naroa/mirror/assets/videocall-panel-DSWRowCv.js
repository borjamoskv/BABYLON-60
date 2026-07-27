class u{constructor(){this.container=null,this.selectedDate=null,this.selectedTime=null,this.formData={}}init(e="contacto-container"){if(this.container=document.getElementById(e),!this.container){Logger.error("[VideoCallPanel] Container not found:",e);return}this.render(),this.bindEvents(),this.initEffects()}getAvailableDates(){const e=[],s=new Date;for(let a=1;a<=14;a++){const t=new Date(s);t.setDate(s.getDate()+a),t.getDay()!==0&&e.push({date:t,dayName:t.toLocaleDateString("es-ES",{weekday:"short"}),dayNum:t.getDate(),monthName:t.toLocaleDateString("es-ES",{month:"short"})})}return e.slice(0,10)}getAvailableSlots(){return[{time:"10:00",label:"10:00"},{time:"11:00",label:"11:00"},{time:"12:00",label:"12:00"},{time:"17:00",label:"17:00"},{time:"18:00",label:"18:00"},{time:"19:00",label:"19:00"}]}render(){const e=this.getAvailableDates();this.getAvailableSlots(),this.container.innerHTML=`
            <div class="videocall-panel">
                <!-- Hero Section -->
                <header class="panel-hero">
                    <div class="hero-content">
                        <span class="hero-badge">📞 CONTACTO DIRECTO</span>
                        <h1 class="hero-title">
                            Hablemos de <span class="text-gradient">Arte</span>
                        </h1>
                        <p class="hero-subtitle">
                            Programa una videollamada con Naroa para conocer su obra, 
                            encargar un retrato personalizado o resolver cualquier duda.
                        </p>
                    </div>
                    <div class="hero-avatar">
                        <img src="images/artworks/the-world-is-yours.webp" 
                             alt="Naroa Gutiérrez Gil"
                             class="avatar-image">
                        <div class="avatar-status">
                            <span class="status-dot"></span>
                            Disponible
                        </div>
                    </div>
                </header>

                <!-- Quick Actions -->
                <section class="quick-actions">
                    <a href="https://wa.me/34600000000?text=Hola%20Naroa,%20me%20interesa%20tu%20obra" 
                       target="_blank" 
                       class="action-card whatsapp magnetic-btn">
                        <div class="action-icon">💬</div>
                        <div class="action-info">
                            <h3>WhatsApp</h3>
                            <p>Respuesta inmediata</p>
                        </div>
                    </a>
                    
                    <a href="mailto:naroa@naroagutierrezgil.com?subject=Consulta%20sobre%20tu%20obra" 
                       class="action-card email magnetic-btn">
                        <div class="action-icon">✉️</div>
                        <div class="action-info">
                            <h3>Email</h3>
                            <p>naroa@naroagutierrezgil.com</p>
                        </div>
                    </a>
                    
                    <button type="button" class="action-card videocall magnetic-btn" id="btn-schedule-call">
                        <div class="action-icon">🎥</div>
                        <div class="action-info">
                            <h3>Videollamada</h3>
                            <p>Programa una cita</p>
                        </div>
                    </button>
                </section>

                <!-- Scheduler Section (initially hidden) -->
                <section class="scheduler-section" id="scheduler-section">
                    <div class="scheduler-card tilt-card">
                        <h2 class="scheduler-title">
                            <span class="title-icon">📅</span>
                            Elige fecha y hora
                        </h2>

                        <!-- Date Picker -->
                        <div class="date-picker">
                            <div class="dates-scroll">
                                ${e.map((s,a)=>`
                                    <button type="button" 
                                            class="date-btn" 
                                            data-date="${s.date.toISOString()}"
                                            style="--delay: ${a*.05}s">
                                        <span class="date-day">${s.dayName}</span>
                                        <span class="date-num">${s.dayNum}</span>
                                        <span class="date-month">${s.monthName}</span>
                                    </button>
                                `).join("")}
                            </div>
                        </div>

                        <!-- Time Slots -->
                        <div class="time-slots" id="time-slots">
                            <p class="slots-hint">Selecciona una fecha primero</p>
                        </div>

                        <!-- Contact Form -->
                        <form class="contact-form" id="contact-form">
                            <div class="form-row">
                                <div class="form-group">
                                    <label for="contact-name">Nombre *</label>
                                    <input type="text" id="contact-name" name="name" required 
                                           placeholder="Tu nombre">
                                </div>
                                <div class="form-group">
                                    <label for="contact-email">Email *</label>
                                    <input type="email" id="contact-email" name="email" required 
                                           placeholder="tu@email.com">
                                </div>
                            </div>
                            
                            <div class="form-group">
                                <label for="contact-interest">¿Qué te interesa?</label>
                                <select id="contact-interest" name="interest">
                                    <option value="">Selecciona una opción</option>
                                    <option value="retrato">Encargar un retrato</option>
                                    <option value="compra">Comprar obra existente</option>
                                    <option value="evento">Evento o exposición</option>
                                    <option value="colaboracion">Colaboración artística</option>
                                    <option value="otro">Otra consulta</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label for="contact-message">Mensaje (opcional)</label>
                                <textarea id="contact-message" name="message" rows="3"
                                          placeholder="Cuéntame más sobre lo que buscas..."></textarea>
                            </div>
                            
                            <button type="submit" class="submit-btn magnetic-btn" id="submit-btn" disabled>
                                <span class="btn-text">Confirmar videollamada</span>
                                <span class="btn-icon">→</span>
                            </button>
                        </form>
                    </div>
                </section>

                <!-- Success Message (hidden) -->
                <section class="success-section" id="success-section" hidden>
                    <div class="success-card">
                        <div class="success-icon">✨</div>
                        <h2>¡Perfecto!</h2>
                        <p class="success-message">
                            Tu videollamada ha sido programada para el 
                            <strong id="confirmed-datetime"></strong>.
                        </p>
                        <p class="success-note">
                            Recibirás un email de confirmación con el enlace de la videollamada.
                        </p>
                        <button type="button" class="back-btn magnetic-btn" id="btn-back">
                            ← Volver a la galería
                        </button>
                    </div>
                </section>

                <!-- Footer -->
                <footer class="panel-footer">
                    <p>
                        ¿Prefieres hablar con MICA primero? 
                        <button type="button" class="mica-link" id="btn-open-mica">
                            Abre el chat →
                        </button>
                    </p>
                </footer>
            </div>
        `}bindEvents(){const e=this.container.querySelector("#btn-schedule-call");e==null||e.addEventListener("click",()=>this.showScheduler()),this.container.querySelectorAll(".date-btn").forEach(i=>{i.addEventListener("click",()=>this.selectDate(i))});const a=this.container.querySelector("#contact-form");a==null||a.addEventListener("submit",i=>this.handleSubmit(i));const t=this.container.querySelector("#btn-back");t==null||t.addEventListener("click",()=>{window.location.hash="#/galeria"});const o=this.container.querySelector("#btn-open-mica");o==null||o.addEventListener("click",()=>{window.micaInstance&&window.micaInstance.toggle()})}showScheduler(){const e=this.container.querySelector("#scheduler-section");e==null||e.classList.add("visible"),e==null||e.scrollIntoView({behavior:"smooth",block:"start"})}selectDate(e){this.container.querySelectorAll(".date-btn").forEach(s=>s.classList.remove("selected")),e.classList.add("selected"),this.selectedDate=new Date(e.dataset.date),this.showTimeSlots()}showTimeSlots(){const e=this.getAvailableSlots(),s=this.container.querySelector("#time-slots");s.innerHTML=`
            <div class="slots-grid">
                ${e.map((a,t)=>`
                    <button type="button" 
                            class="time-btn" 
                            data-time="${a.time}"
                            style="--delay: ${t*.05}s">
                        ${a.label}
                    </button>
                `).join("")}
            </div>
        `,s.querySelectorAll(".time-btn").forEach(a=>{a.addEventListener("click",()=>this.selectTime(a))})}selectTime(e){this.container.querySelectorAll(".time-btn").forEach(s=>s.classList.remove("selected")),e.classList.add("selected"),this.selectedTime=e.dataset.time,this.updateSubmitButton()}updateSubmitButton(){const e=this.container.querySelector("#submit-btn"),s=this.container.querySelector("#contact-name"),a=this.container.querySelector("#contact-email"),t=this.selectedDate&&this.selectedTime&&(s==null?void 0:s.value.trim())&&(a==null?void 0:a.value.trim());e.disabled=!t}handleSubmit(e){e.preventDefault();const s=e.target,a=new FormData(s);this.formData={name:a.get("name"),email:a.get("email"),interest:a.get("interest"),message:a.get("message"),date:this.selectedDate,time:this.selectedTime};const t=this.selectedDate.toLocaleDateString("es-ES",{weekday:"long",day:"numeric",month:"long"}),o=this.container.querySelector("#confirmed-datetime");o.textContent=`${t} a las ${this.selectedTime}`,this.showSuccess()}showSuccess(){var e,s,a;(e=this.container.querySelector("#scheduler-section"))==null||e.classList.remove("visible"),(s=this.container.querySelector(".quick-actions"))==null||s.classList.add("hidden"),(a=this.container.querySelector("#success-section"))==null||a.removeAttribute("hidden")}initEffects(){this.container.querySelectorAll(".magnetic-btn").forEach(t=>{t.addEventListener("mousemove",o=>{const i=t.getBoundingClientRect(),n=o.clientX-i.left-i.width/2,c=o.clientY-i.top-i.height/2;t.style.transform=`translate(${n*.2}px, ${c*.2}px)`}),t.addEventListener("mouseleave",()=>{t.style.transform="translate(0, 0)"})}),this.container.querySelectorAll("input, textarea, select").forEach(t=>{t.addEventListener("input",()=>this.updateSubmitButton())}),this.container.querySelectorAll(".tilt-card").forEach(t=>{t.addEventListener("mousemove",o=>{const i=t.getBoundingClientRect(),n=o.clientX-i.left,c=o.clientY-i.top,l=i.width/2,r=i.height/2,d=(c-r)/30,m=(l-n)/30;t.style.transform=`perspective(1000px) rotateX(${d}deg) rotateY(${m}deg)`}),t.addEventListener("mouseleave",()=>{t.style.transform="perspective(1000px) rotateX(0) rotateY(0)"})})}destroy(){}}const p=new u;export{u as VideoCallPanel,p as videoCallPanel};
