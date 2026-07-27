class RestauradorGame {
    constructor() {
        this.canvas = null;
        this.ctx = null;
        this.active = false;
        this.painting = null;
        this.brushColor = '#8B4513';
        this.brushSize = 15;
        this.damage = 0;
        this.brushMode = 'paint'; // paint, stamp, spray
        this.audioCtx = null;
    }

    init() {
        const container = document.getElementById("restaurador-game-container");
        if (!container) return;

        container.textContent = "";
        container.insertAdjacentHTML("afterbegin", `
          <div class="restaurador-wrapper" style="
              background: #0a0a0a; 
              border: 1px solid #333; 
              border-radius: 12px; 
              padding: 24px; 
              box-shadow: 0 10px 30px rgba(0,0,0,0.5);
              max-width: 650px;
              margin: 0 auto;
              font-family: 'Inter', sans-serif;
              color: #eaeaea;
          ">
            <div class="game-header" style="text-align: center; margin-bottom: 20px;">
              <h2 style="margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.5px;">
                <span style="color: #2B3BE5;">👨‍🎨</span> El Restaurador Desastroso
              </h2>
              <p style="margin: 8px 0 0 0; font-size: 14px; color: #888;">
                Demuestra tu talento. Destruye... digo, restaura la obra maestra.
              </p>
            </div>
            
            <div class="canvas-container" style="
                position: relative; 
                border-radius: 8px; 
                overflow: hidden;
                box-shadow: inset 0 0 0 1px #333;
                background: #111;
                margin-bottom: 20px;
            ">
                <canvas id="restaurador-canvas" width="600" height="500" style="display: block; width: 100%; cursor: crosshair;"></canvas>
            </div>

            <div class="controls" style="
                display: flex; 
                gap: 12px; 
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            ">
                 <div class="tools" style="display: flex; gap: 8px; align-items: center;">
                     <button class="tool-btn color-btn" data-color="#8B4513" style="background: #8B4513; width: 32px; height: 32px; border-radius: 50%; border: 2px solid #2B3BE5; cursor: pointer;"></button>
                     <button class="tool-btn color-btn" data-color="#ff0044" style="background: #ff0044; width: 32px; height: 32px; border-radius: 50%; border: 2px solid transparent; cursor: pointer;"></button>
                     <button class="tool-btn color-btn" data-color="#000000" style="background: #000000; width: 32px; height: 32px; border-radius: 50%; border: 2px solid transparent; cursor: pointer;"></button>
                     <button class="tool-btn color-btn" data-color="#f4e0c8" style="background: #f4e0c8; width: 32px; height: 32px; border-radius: 50%; border: 2px solid transparent; cursor: pointer;"></button>
                     <input type="range" id="brush-size" min="5" max="50" value="15" style="margin-left: 12px; accent-color: #2B3BE5;">
                     <select id="brush-mode" style="background: #111; color: #aaa; border: 1px solid #444; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 500; font-family: inherit; margin-left: 8px;">
                         <option value="paint">🎨 Pincel</option>
                         <option value="spray">💨 Spray</option>
                         <option value="stamp">🐵 Ecce Homo</option>
                     </select>
                 </div>
                 
                 <div class="actions" style="display: flex; gap: 12px;">
                     <button id="reset-btn" style="
                         background: transparent; 
                         color: #aaa; 
                         border: 1px solid #444; 
                         padding: 8px 16px; 
                         border-radius: 6px; 
                         cursor: pointer;
                         font-weight: 500;
                         transition: all 0.2s ease;
                     ">Limpiar</button>
                     <button id="download-btn" style="
                         background: transparent; 
                         color: #fff; 
                         border: 1px solid #2B3BE5; 
                         padding: 8px 16px; 
                         border-radius: 6px; 
                         cursor: pointer;
                         font-weight: 500;
                     ">Exportar</button>
                     <button id="mint-btn" style="
                         background: #2B3BE5; 
                         color: white; 
                         border: none; 
                         padding: 8px 16px; 
                         border-radius: 6px; 
                         cursor: pointer;
                         font-weight: 600;
                         transition: all 0.2s ease;
                     ">Inmortalizar (NFT)</button>
                 </div>
            </div>
            
            <div class="damage-container" style="margin-top: 20px; background: #222; height: 16px; border-radius: 8px; overflow: hidden; position: relative; border: 1px solid #333;">
                <div id="damage-bar" style="width: 0%; height: 100%; background: linear-gradient(90deg, #2B3BE5, #ff0044); transition: width 0.2s;"></div>
                <span style="position: absolute; left: 0; right: 0; top: 0; text-align: center; font-size: 11px; font-weight: 700; color: #fff; line-height: 16px; pointer-events: none; text-shadow: 0 1px 2px rgba(0,0,0,0.8); letter-spacing: 1px;">NIVEL DE DESASTRE</span>
            </div>
          </div>
        `);

        this.canvas = document.getElementById("restaurador-canvas");
        this.ctx = this.canvas.getContext("2d", { willReadFrequently: true });
        
        this.setupEvents();
        this.loadBaseImage();
    }

    setupEvents() {
        const container = document.getElementById("restaurador-game-container");
        
        let isDrawing = false;
        let lastX = 0;
        let lastY = 0;

        const startDrawing = (e) => {
            isDrawing = true;
            const pos = this.getPointerPos(e);
            lastX = pos.x;
            lastY = pos.y;
            this.draw(pos.x, pos.y, false);
        };

        const stopDrawing = () => { isDrawing = false; this.ctx.beginPath(); };

        const drawEvent = (e) => {
            if (!isDrawing) return;
            e.preventDefault();
            const pos = this.getPointerPos(e);
            this.draw(pos.x, pos.y, true, lastX, lastY);
            lastX = pos.x;
            lastY = pos.y;
        };

        this.canvas.addEventListener("mousedown", startDrawing);
        this.canvas.addEventListener("mousemove", drawEvent);
        this.canvas.addEventListener("mouseup", stopDrawing);
        this.canvas.addEventListener("mouseout", stopDrawing);

        // Touch support
        this.canvas.addEventListener("touchstart", startDrawing, {passive: false});
        this.canvas.addEventListener("touchmove", drawEvent, {passive: false});
        this.canvas.addEventListener("touchend", stopDrawing);

        // Tool selection
        container.querySelectorAll('.color-btn').forEach(btn => {
            btn.addEventListener('click', (e) => {
                container.querySelectorAll('.color-btn').forEach(b => b.style.borderColor = 'transparent');
                e.target.style.borderColor = '#2B3BE5';
                this.brushColor = e.target.dataset.color;
            });
        });

        document.getElementById('brush-size').addEventListener('input', (e) => {
            this.brushSize = parseInt(e.target.value);
        });

        document.getElementById('brush-mode').addEventListener('change', (e) => {
            this.brushMode = e.target.value;
        });

        document.getElementById('reset-btn').addEventListener('click', () => {
            this.damage = 0;
            document.getElementById('damage-bar').style.width = '0%';
            this.drawBase();
        });

        document.getElementById('download-btn').addEventListener('click', () => {
            const link = document.createElement('a');
            link.download = 'ecce-homo-masterpiece.png';
            link.href = this.canvas.toDataURL('image/png');
            link.click();
        });

        container.querySelector("#mint-btn").addEventListener("click", (e) => {
            const btn = e.target;
            btn.textContent = "¡Vendido por 69M ETH!";
            btn.style.background = "#10B981";
            
            setTimeout(() => {
                if(window.RestauradorWeb3) {
                    window.RestauradorWeb3.mintNFT(this.canvas.toDataURL());
                } else {
                    alert("Obra maestra guardada en la blockchain imaginaria.\\n¡Felicidades, restaurador!");
                }
                btn.textContent = "Inmortalizar (NFT)";
                btn.style.background = "#2B3BE5";
            }, 1500);
        });
    }

    initAudio() {
        if (!this.audioCtx) {
            this.audioCtx = new (window.AudioContext || window.webkitAudioContext)();
        }
    }

    playSplatSound() {
        try {
            this.initAudio();
            if (this.audioCtx.state === 'suspended') {
                this.audioCtx.resume();
            }
            
            const osc = this.audioCtx.createOscillator();
            const gain = this.audioCtx.createGain();
            
            osc.connect(gain);
            gain.connect(this.audioCtx.destination);
            
            // Synthesize a squishy wet paint splat sound
            osc.type = 'sine';
            const now = this.audioCtx.currentTime;
            
            osc.frequency.setValueAtTime(150, now);
            osc.frequency.exponentialRampToValueAtTime(40, now + 0.15);
            
            gain.gain.setValueAtTime(0.15, now);
            gain.gain.exponentialRampToValueAtTime(0.01, now + 0.15);
            
            osc.start(now);
            osc.stop(now + 0.15);
        } catch(e) {
            // Audio context permission or support issues
        }
    }

    getPointerPos(e) {
        const rect = this.canvas.getBoundingClientRect();
        const clientX = e.touches ? e.touches[0].clientX : e.clientX;
        const clientY = e.touches ? e.touches[0].clientY : e.clientY;
        return {
            x: (clientX - rect.left) * (this.canvas.width / rect.width),
            y: (clientY - rect.top) * (this.canvas.height / rect.height)
        };
    }

    draw(x, y, isContinuous, lastX, lastY) {
        this.playSplatSound();
        this.ctx.lineWidth = this.brushSize;
        this.ctx.lineCap = 'round';
        this.ctx.lineJoin = 'round';
        this.ctx.strokeStyle = this.brushColor;
        this.ctx.fillStyle = this.brushColor;
        this.ctx.globalAlpha = 0.8;

        if (this.brushMode === 'paint') {
            if (isContinuous) {
                this.ctx.beginPath();
                this.ctx.moveTo(lastX, lastY);
                const jitter = (Math.random() - 0.5) * (this.brushSize * 0.3);
                this.ctx.lineTo(x + jitter, y + jitter);
                this.ctx.stroke();
            } else {
                this.ctx.beginPath();
                this.ctx.arc(x, y, this.brushSize / 2, 0, Math.PI * 2);
                this.ctx.fill();
            }
        } else if (this.brushMode === 'spray') {
            const density = 30;
            this.ctx.globalAlpha = 0.5;
            for (let i = 0; i < density; i++) {
                const angle = Math.random() * Math.PI * 2;
                const radius = Math.random() * this.brushSize;
                const sx = x + Math.cos(angle) * radius;
                const sy = y + Math.sin(angle) * radius;
                this.ctx.fillRect(sx, sy, 1.5, 1.5);
            }
        } else if (this.brushMode === 'stamp') {
            // Draw a hilarious abstract monkey-like face (deformed restoration helper)
            this.ctx.save();
            this.ctx.translate(x, y);
            this.ctx.globalAlpha = 0.95;
            
            const r = this.brushSize * 1.2;
            
            // Deformed head
            this.ctx.fillStyle = '#8B4513';
            this.ctx.beginPath();
            this.ctx.arc(0, 0, r, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Muzzle area
            this.ctx.fillStyle = '#f4e0c8';
            this.ctx.beginPath();
            this.ctx.ellipse(0, r * 0.3, r * 0.8, r * 0.5, 0, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Strange eyes
            this.ctx.fillStyle = '#fff';
            this.ctx.beginPath();
            this.ctx.arc(-r * 0.3, -r * 0.2, r * 0.22, 0, Math.PI * 2);
            this.ctx.arc(r * 0.3, -r * 0.2, r * 0.22, 0, Math.PI * 2);
            this.ctx.fill();
            
            this.ctx.fillStyle = '#000';
            this.ctx.beginPath();
            this.ctx.arc(-r * 0.28, -r * 0.2, r * 0.08, 0, Math.PI * 2);
            this.ctx.arc(r * 0.32, -r * 0.2, r * 0.08, 0, Math.PI * 2);
            this.ctx.fill();
            
            // Horrifying red lips/mouth
            this.ctx.strokeStyle = '#ff0044';
            this.ctx.lineWidth = Math.max(2, r * 0.1);
            this.ctx.beginPath();
            this.ctx.arc(0, r * 0.2, r * 0.3, 0.1 * Math.PI, 0.9 * Math.PI);
            this.ctx.stroke();
            
            this.ctx.restore();
        }
        
        this.ctx.globalAlpha = 1.0;
        
        // Update damage meter
        const increment = this.brushMode === 'stamp' ? 6 : (this.brushSize * 0.05);
        this.damage += increment;
        let percent = Math.min(100, this.damage);
        document.getElementById('damage-bar').style.width = percent + '%';
        
        if(percent >= 100 && this.damage < 110) { 
            this.damage = 150; // Prevent multiple alerts
            setTimeout(() => alert("¡Cecilia Giménez estaría orgullosa de ti! Nivel de desastre absoluto alcanzado."), 100);
        }
    }

    loadBaseImage() {
        // Try to load a real image from the site
        const img = new Image();
        img.crossOrigin = "Anonymous";
        // Attempting to load an artwork to deface, fallback to CSS placeholder if it fails
        img.onload = () => {
            this.painting = img;
            this.drawBase();
        };
        img.onerror = () => {
            this.painting = null;
            this.drawBase();
        };
        // This image path must exist in the deployed site (we use marilyn-rocks as it's guaranteed to be built)
        img.src = "/images/obra/marilyn-rocks.webp";
    }

    drawBase() {
        // Fill background
        this.ctx.fillStyle = "#EAE6DF";
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        if (this.painting) {
            // Calculate aspect ratio fit
            const hRatio = this.canvas.width / this.painting.width;
            const vRatio = this.canvas.height / this.painting.height;
            const ratio  = Math.min(hRatio, vRatio) * 0.9;
            const centerShift_x = (this.canvas.width - this.painting.width * ratio) / 2;
            const centerShift_y = (this.canvas.height - this.painting.height * ratio) / 2;  
            
            // Add a nice frame
            this.ctx.fillStyle = "#222";
            this.ctx.fillRect(
                centerShift_x - 10, 
                centerShift_y - 10, 
                this.painting.width * ratio + 20, 
                this.painting.height * ratio + 20
            );

            this.ctx.drawImage(
                this.painting, 0, 0, this.painting.width, this.painting.height,
                centerShift_x, centerShift_y, this.painting.width * ratio, this.painting.height * ratio
            );
        } else {
            // Fallback if image fails to load
            this.ctx.fillStyle = "#222";
            this.ctx.fillRect(100, 50, 400, 400);
            
            this.ctx.fillStyle = "#fff";
            this.ctx.font = "80px Inter";
            this.ctx.textAlign = "center";
            this.ctx.textBaseline = "middle";
            this.ctx.fillText("🖼️", 300, 220);
            
            this.ctx.font = "bold 24px Inter";
            this.ctx.fillText("Pintura Inestimable", 300, 300);
            
            this.ctx.font = "16px Inter";
            this.ctx.fillStyle = "#aaa";
            this.ctx.fillText("Lista para ser destruida", 300, 340);
        }
    }
}

// Initialize on DOM load
document.addEventListener("DOMContentLoaded", () => {
    window.RestauradorGame = new RestauradorGame();
    window.RestauradorGame.init();
});
