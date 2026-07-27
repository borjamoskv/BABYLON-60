// telemetry.js - C5-REAL Hardware/Audio Sensor for Naroa Vision
import gsap from 'gsap';

export class KintsugiTelemetry {
    constructor(material) {
        this.material = material;
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        this.analyser = this.audioContext.createAnalyser();
        this.analyser.fftSize = 256;
        this.dataArray = new Uint8Array(this.analyser.frequencyBinCount);
        
        // Linking visual output to MOSKV-1 hardware exergy via WebSockets
        this.ws = new WebSocket('ws://localhost:8080/telemetry');
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.entropy) {
                this.applyEntropyDistortion(data.entropy);
            }
        };
    }

    startAudioAnalysis(stream) {
        const source = this.audioContext.createMediaStreamSource(stream);
        source.connect(this.analyser);
        this.updateAudioLoop();
    }

    updateAudioLoop() {
        this.analyser.getByteFrequencyData(this.dataArray);
        let sum = 0;
        for (let i = 0; i < this.dataArray.length; i++) {
            sum += this.dataArray[i];
        }
        let avg = sum / this.dataArray.length;
        
        // Map average audio volume to Liquid Zoom progress shader uniform
        if (this.material && this.material.uniforms) {
            let targetProgress = avg / 255.0;
            gsap.to(this.material.uniforms.progress, { value: targetProgress, duration: 0.1 });
        }
        
        requestAnimationFrame(() => this.updateAudioLoop());
    }

    applyEntropyDistortion(entropyLevel) {
        // Higher CPU entropy forces RGB shift distortion spikes (Phenomenon obeying Noumenon)
        if (entropyLevel > 3.0 && this.material) {
            gsap.to(this.material.uniforms.progress, { value: 1.0, duration: 0.2, yoyo: true, repeat: 1 });
        }
    }
}
