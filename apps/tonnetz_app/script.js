// Draw the Tonnetz Grid using SVG
function drawTonnetz() {
    const container = document.getElementById('tonnetz-container');
    const width = container.clientWidth;
    const height = container.clientHeight;
    
    // Hexagonal grid parameters
    const size = 40;
    const dx = size * Math.cos(Math.PI / 6);
    const dy = size * 1.5;
    
    let svg = `<svg width="100%" height="100%" viewBox="0 0 ${width} ${height}">`;
    
    // Grid Lines (triangular)
    svg += `<g stroke="rgba(255,255,255,0.05)" stroke-width="1">`;
    for(let i = -10; i < 20; i++) {
        for(let j = -10; j < 20; j++) {
            const cx = width/2 + (i + (j%2?0.5:0)) * dx * 2;
            const cy = height/2 + j * dy;
            
            // horizontal/diagonal connections
            const cxRight = cx + dx*2;
            const cyRight = cy;
            const cxBottomRight = cx + dx;
            const cyBottomRight = cy + dy;
            const cxBottomLeft = cx - dx;
            const cyBottomLeft = cy + dy;
            
            svg += `<line x1="${cx}" y1="${cy}" x2="${cxRight}" y2="${cyRight}" />`;
            svg += `<line x1="${cx}" y1="${cy}" x2="${cxBottomRight}" y2="${cyBottomRight}" />`;
            svg += `<line x1="${cx}" y1="${cy}" x2="${cxBottomLeft}" y2="${cyBottomLeft}" />`;
        }
    }
    svg += `</g>`;

    // Nodes
    const notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'];
    let noteIdx = 0;
    
    svg += `<g fill="#8b949e" font-family="'JetBrains Mono', monospace" font-size="10" text-anchor="middle" dominant-baseline="middle">`;
    for(let i = -5; i < 10; i++) {
        for(let j = -5; j < 10; j++) {
            const cx = width/2 + (i + (j%2?0.5:0)) * dx * 2;
            const cy = height/2 + j * dy;
            
            // Randomly skip some outer nodes for aesthetic
            if (cx < -50 || cx > width+50 || cy < -50 || cy > height+50) continue;
            
            svg += `<circle cx="${cx}" cy="${cy}" r="3" fill="rgba(255,255,255,0.1)"/>`;
            svg += `<text x="${cx}" y="${cy - 12}">${notes[Math.abs((i*7 + j*4)%12)]}</text>`;
        }
    }
    svg += `</g>`;
    
    // Highlight A minor triad (A, C, E)
    const cxA = width/2;
    const cyA = height/2;
    const cxC = cxA - dx;
    const cyC = cyA + dy;
    const cxE = cxA + dx;
    const cyE = cyA + dy;
    
    svg += `<polygon points="${cxA},${cyA} ${cxC},${cyC} ${cxE},${cyE}" 
            fill="rgba(59, 130, 246, 0.2)" 
            stroke="#3b82f6" 
            stroke-width="2" 
            style="filter: drop-shadow(0 0 10px rgba(59,130,246,0.8));"/>`;
            
    // Central Node Highlight
    svg += `<circle cx="${cxA}" cy="${cyA}" r="5" fill="#3b82f6" />`;
    svg += `<text x="${cxA}" y="${cyA}" fill="#fff" font-family="'Inter', sans-serif" font-weight="bold" font-size="14" text-anchor="middle" dominant-baseline="middle">Am</text>`;
    
    svg += `</svg>`;
    container.innerHTML = svg;
}

// Draw Euclidean Rings
function drawRings() {
    const canvas = document.getElementById('euclidean-canvas');
    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    
    const cx = canvas.width / 2;
    const cy = canvas.height / 2;
    
    const rings = [
        { r: 30, dots: 4, active: [0, 2], color: '#f59e0b' },
        { r: 50, dots: 8, active: [0, 3, 5], color: '#ec4899' },
        { r: 70, dots: 16, active: [0, 2, 4, 7, 9, 12, 14], color: '#3b82f6' },
        { r: 90, dots: 12, active: [0, 3, 6, 9], color: '#10b981' }
    ];
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    rings.forEach((ring, idx) => {
        // Draw track
        ctx.beginPath();
        ctx.arc(cx, cy, ring.r, 0, Math.PI * 2);
        ctx.strokeStyle = 'rgba(255,255,255,0.05)';
        ctx.lineWidth = 1;
        ctx.stroke();
        
        // Draw dots
        for(let i=0; i<ring.dots; i++) {
            const angle = (i / ring.dots) * Math.PI * 2 - Math.PI/2;
            const x = cx + Math.cos(angle) * ring.r;
            const y = cy + Math.sin(angle) * ring.r;
            
            ctx.beginPath();
            ctx.arc(x, y, 3, 0, Math.PI * 2);
            if (ring.active.includes(i)) {
                ctx.fillStyle = ring.color;
                ctx.shadowColor = ring.color;
                ctx.shadowBlur = 10;
            } else {
                ctx.fillStyle = 'rgba(255,255,255,0.1)';
                ctx.shadowBlur = 0;
            }
            ctx.fill();
        }
    });
    
    // Playhead line
    ctx.shadowBlur = 0;
    ctx.beginPath();
    ctx.moveTo(cx, cy);
    ctx.lineTo(cx, cy - 100);
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.setLineDash([5, 5]);
    ctx.stroke();
    ctx.setLineDash([]);
}

// Draw Arrangement Timeline
function drawArrangement() {
    const canvas = document.getElementById('arrangement-canvas');
    const ctx = canvas.getContext('2d');
    const container = canvas.parentElement;
    
    canvas.width = container.clientWidth;
    canvas.height = container.clientHeight;
    
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    
    // Grid
    const tracks = 4;
    const trackHeight = canvas.height / tracks;
    
    ctx.strokeStyle = 'rgba(255,255,255,0.05)';
    ctx.lineWidth = 1;
    for(let i = 1; i < tracks; i++) {
        ctx.beginPath();
        ctx.moveTo(0, i * trackHeight);
        ctx.lineTo(canvas.width, i * trackHeight);
        ctx.stroke();
    }
    
    // Random notes
    const colors = ['#ec4899', '#3b82f6', '#10b981', '#f59e0b'];
    
    for(let t = 0; t < tracks; t++) {
        const yOffset = t * trackHeight;
        const color = colors[t];
        
        for(let i = 0; i < 40; i++) {
            if (Math.random() > 0.3) {
                const x = i * (canvas.width / 40);
                const y = yOffset + 10 + Math.random() * (trackHeight - 20);
                const w = Math.random() * 15 + 5;
                const h = 4;
                
                ctx.fillStyle = color;
                ctx.globalAlpha = 0.8;
                ctx.fillRect(x, y, w, h);
            }
        }
    }
    
    // Playhead
    ctx.globalAlpha = 1;
    ctx.beginPath();
    ctx.moveTo(canvas.width * 0.2, 0);
    ctx.lineTo(canvas.width * 0.2, canvas.height);
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = 1;
    ctx.stroke();
}

window.addEventListener('resize', () => {
    drawTonnetz();
    drawRings();
    drawArrangement();
});

// Initial draw
setTimeout(() => {
    drawTonnetz();
    drawRings();
    drawArrangement();
}, 100);
