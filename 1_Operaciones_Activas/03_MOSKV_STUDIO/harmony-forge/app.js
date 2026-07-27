// --- HARMONY FORGE // ДЕКОДЕР-9 ---

// Music Theory Tables (21-EDO / 21-TET microtonal framework)
const ROOT_FREQS = {
    "A": 220.00,  // A3 base
    "C": 130.81,  // C3 base
    "D": 146.83,  // D3 base
    "E": 164.81,  // E3 base
    "G": 196.00   // G3 base
};

const SCALES = {
    pentatonic_minor: [0, 5, 9, 12, 17], // Approximates minor pentatonic in 21-EDO
    pentatonic_major: [0, 4, 7, 12, 16], // Approximates major pentatonic in 21-EDO
    dorian: [0, 4, 5, 9, 12, 16, 17],    // Dorian Mode EDO-21
    phrygian_dominant: [0, 2, 7, 9, 12, 14, 17] // Soviet relic mode in EDO-21
};

// Chord progressions (represented by scale index offsets)
const PROGRESSIONS = {
    minor: [
        [0, 2, 3], // i
        [3, 4, 0], // VI
        [4, 1, 3], // VII
        [2, 3, 0]  // v
    ],
    major: [
        [0, 2, 4], // I
        [4, 0, 2], // V
        [1, 3, 4], // vi
        [3, 4, 0]  // IV
    ]
};

// State Variables
let audioCtx = null;
let masterGain = null;
let delayNode = null;
let reverbNode = null;
let noiseNode = null;
let isPlaying = true;
let currentBpm = 90;
let currentRoot = "A";
let currentScaleType = "pentatonic_minor";
let wowFlutterAmount = 0.25;
let tapeWearAmount = 0.35;
let filterCutoff = 800;

// Wow & Flutter Global Modulators
let wowLfo = null;
let wowLfoGain = null;
let flutterLfo = null;
let flutterLfoGain = null;
let masterWowFlutterDelay = null;

// Systems state variables
let enableDrums = false;
let enableTrumpet = true;
let enableTheremin = true;
let enableGuitar = true;
let isNegativeHarmony = false;
let isFractalMode = false;
let drumIntervalId = null;
let drumTickCount = 0;
let lastSequencerBpm = 90;

// Sequencer & Time
let tapeCounterSecs = 0;
let lastProgressTime = 0;
let activeChordIdx = 0;
let padIntervalId = null;

// UI Elements
const playBtn = document.getElementById("play-btn");
const rootSelect = document.getElementById("root-select");
const scaleSelect = document.getElementById("scale-select");
const tempoSlider = document.getElementById("tempo-slider");
const tempoVal = document.getElementById("tempo-val");
const wowFlutterSlider = document.getElementById("wow-flutter-slider");
const wowFlutterVal = document.getElementById("wow-flutter-val");
const tapeWearSlider = document.getElementById("tape-wear-slider");
const tapeWearVal = document.getElementById("tape-wear-val");
const filterCutoffSlider = document.getElementById("filter-cutoff-slider");
const filterCutoffVal = document.getElementById("filter-cutoff-val");
const delaySlider = document.getElementById("delay-slider");
const delayVal = document.getElementById("delay-val");
const reverbSlider = document.getElementById("reverb-slider");
const reverbVal = document.getElementById("reverb-val");

const enablePadCheckbox = document.getElementById("enable-pad");
const enablePluckCheckbox = document.getElementById("enable-pluck");
const enableBellCheckbox = document.getElementById("enable-bell");
const enableTrumpetCheckbox = document.getElementById("enable-trumpet");
const enableThereminCheckbox = document.getElementById("enable-theremin");
const enableGuitarCheckbox = document.getElementById("enable-guitar");
const enableDrumsCheckbox = document.getElementById("enable-drums");
const negativeHarmonyCheckbox = document.getElementById("negative-harmony");
const fractalModeCheckbox = document.getElementById("fractal-mode");

const statusText = document.getElementById("status-text");
const pulseDot = document.querySelector(".pulse-dot");
const tapeCounter = document.getElementById("tape-counter");
const trackingText = document.getElementById("tracking-text");

// Canvas Physics Nodes Setup
const sandboxCanvas = document.getElementById("sandbox-canvas");
const ctxSandbox = sandboxCanvas.getContext("2d");
let balls = [];
const GRAVITY = 0.15;
const FRICTION = 0.99;

// Oscilloscope Canvas
const visualizerCanvas = document.getElementById("visualizer-canvas");
const ctxVisualizer = visualizerCanvas.getContext("2d");
let analyser = null;
let dataArray = null;

// Presets
// Presets & Reels selection
const leftReel = document.getElementById("left-reel");
const rightReel = document.getElementById("right-reel");

const presetSlow = document.getElementById("preset-slow");
const presetFast = document.getElementById("preset-fast");
const presetEntropy = document.getElementById("preset-entropy");

presetSlow.addEventListener("click", () => {
    setActivePreset(presetSlow);
    applyPreset("slow");
});
presetFast.addEventListener("click", () => {
    setActivePreset(presetFast);
    applyPreset("fast");
});
if (presetEntropy) {
    presetEntropy.addEventListener("click", () => {
        setActivePreset(presetEntropy);
        applyPreset("entropy");
    });
}

function setActivePreset(selectedEl) {
    [presetSlow, presetFast, presetEntropy].forEach(el => {
        if (el) el.classList.remove("active");
    });
    selectedEl.classList.add("active");
}

document.getElementById("clear-nodes").addEventListener("click", () => { balls = []; });

function applyPreset(type) {
    if (type === "slow") {
        tempoSlider.value = 75;
        wowFlutterSlider.value = 60;
        tapeWearSlider.value = 50;
        filterCutoffSlider.value = 500;
        delaySlider.value = 65;
        reverbSlider.value = 80;
        enablePadCheckbox.checked = true;
        enablePluckCheckbox.checked = false;
        enableBellCheckbox.checked = true;
        enableTrumpetCheckbox.checked = false;
        enableThereminCheckbox.checked = true;
        enableGuitarCheckbox.checked = true;
        enableDrumsCheckbox.checked = false;
        negativeHarmonyCheckbox.checked = false;
        fractalModeCheckbox.checked = false;
    } else if (type === "fast") {
        tempoSlider.value = 120;
        wowFlutterSlider.value = 15;
        tapeWearSlider.value = 15;
        filterCutoffSlider.value = 1800;
        delaySlider.value = 25;
        reverbSlider.value = 30;
        enablePadCheckbox.checked = true;
        enablePluckCheckbox.checked = true;
        enableBellCheckbox.checked = true;
        enableTrumpetCheckbox.checked = true;
        enableThereminCheckbox.checked = false;
        enableGuitarCheckbox.checked = false;
        enableDrumsCheckbox.checked = true;
        negativeHarmonyCheckbox.checked = false;
        fractalModeCheckbox.checked = false;
    } else if (type === "entropy") {
        tempoSlider.value = 55;
        wowFlutterSlider.value = 85;
        tapeWearSlider.value = 90;
        filterCutoffSlider.value = 280;
        delaySlider.value = 85;
        reverbSlider.value = 95;
        enablePadCheckbox.checked = true;
        enablePluckCheckbox.checked = true;
        enableBellCheckbox.checked = false;
        enableTrumpetCheckbox.checked = true;
        enableThereminCheckbox.checked = true;
        enableGuitarCheckbox.checked = true;
        enableDrumsCheckbox.checked = true;
        negativeHarmonyCheckbox.checked = true;
        fractalModeCheckbox.checked = true;
    }
    
    // Sync variables with checkboxes
    enableTrumpet = enableTrumpetCheckbox.checked;
    enableTheremin = enableThereminCheckbox.checked;
    enableGuitar = enableGuitarCheckbox.checked;
    enableDrums = enableDrumsCheckbox.checked;
    isNegativeHarmony = negativeHarmonyCheckbox.checked;
    isFractalMode = fractalModeCheckbox.checked;
    
    updateSliderValues();
    
    if (isPlaying && audioCtx && lowpassNode) {
        updatePadChord(lowpassNode);
    }
}

function updateSliderValues() {
    currentBpm = parseInt(tempoSlider.value);
    tempoVal.textContent = currentBpm;
    
    wowFlutterAmount = parseInt(wowFlutterSlider.value) / 100;
    wowFlutterVal.textContent = wowFlutterSlider.value + "%";
    
    tapeWearAmount = parseInt(tapeWearSlider.value) / 100;
    tapeWearVal.textContent = tapeWearSlider.value + "%";
    
    filterCutoff = parseInt(filterCutoffSlider.value);
    filterCutoffVal.textContent = filterCutoff + " Hz";
    
    delayVal.textContent = delaySlider.value + "%";
    reverbVal.textContent = reverbSlider.value + "%";
    
    if (audioCtx) {
        if (delayNode) {
            delayNode.gainNode.gain.setTargetAtTime(parseInt(delaySlider.value) / 100 * 0.5, audioCtx.currentTime, 0.1);
        }
        if (reverbNode) {
            reverbNode.gain.setTargetAtTime(parseInt(reverbSlider.value) / 100 * 0.6, audioCtx.currentTime, 0.1);
        }
        if (noiseNode) {
            noiseNode.gain.gain.setTargetAtTime(tapeWearAmount * 0.15, audioCtx.currentTime, 0.2);
        }
        if (wowLfoGain) {
            wowLfoGain.gain.setTargetAtTime(wowFlutterAmount * 0.003, audioCtx.currentTime, 0.1);
        }
        if (flutterLfoGain) {
            flutterLfoGain.gain.setTargetAtTime(wowFlutterAmount * 0.0006, audioCtx.currentTime, 0.1);
        }
    }

    // Dynamic drum speed restart
    if (isPlaying && enableDrums) {
        startDrumSequencer();
    }
}

// Add event listeners to sliders
[tempoSlider, wowFlutterSlider, tapeWearSlider, filterCutoffSlider, delaySlider, reverbSlider].forEach(slider => {
    slider.addEventListener("input", updateSliderValues);
});

rootSelect.addEventListener("change", () => { currentRoot = rootSelect.value; });
scaleSelect.addEventListener("change", () => { currentScaleType = scaleSelect.value; });

enableTrumpetCheckbox.addEventListener("change", (e) => { enableTrumpet = e.target.checked; });
enableThereminCheckbox.addEventListener("change", (e) => { enableTheremin = e.target.checked; });
enableGuitarCheckbox.addEventListener("change", (e) => { enableGuitar = e.target.checked; });
enableDrumsCheckbox.addEventListener("change", (e) => { 
    enableDrums = e.target.checked; 
    if (isPlaying && enableDrums) {
        startDrumSequencer();
    } else if (!enableDrums && drumIntervalId) {
        clearInterval(drumIntervalId);
        drumIntervalId = null;
    }
});
negativeHarmonyCheckbox.addEventListener("change", (e) => { isNegativeHarmony = e.target.checked; });
fractalModeCheckbox.addEventListener("change", (e) => { isFractalMode = e.target.checked; });

// Initialize Web Audio API
function initAudio() {
    audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    
    // Master Gain
    masterGain = audioCtx.createGain();
    masterGain.gain.setValueAtTime(0.8, audioCtx.currentTime);
    
    // Filter
    const lowpass = audioCtx.createBiquadFilter();
    lowpass.type = "lowpass";
    lowpass.frequency.setValueAtTime(filterCutoff, audioCtx.currentTime);
    lowpass.Q.setValueAtTime(1, audioCtx.currentTime);
    
    // Analyser
    analyser = audioCtx.createAnalyser();
    analyser.fftSize = 512;
    dataArray = new Uint8Array(analyser.frequencyBinCount);

    // Wow & Flutter Master Delay (Doppler tape emulation)
    masterWowFlutterDelay = audioCtx.createDelay(1.0);
    masterWowFlutterDelay.delayTime.setValueAtTime(0.015, audioCtx.currentTime);
    
    wowLfo = audioCtx.createOscillator();
    wowLfo.type = "sine";
    wowLfo.frequency.setValueAtTime(0.55, audioCtx.currentTime);
    
    wowLfoGain = audioCtx.createGain();
    wowLfoGain.gain.setValueAtTime(wowFlutterAmount * 0.003, audioCtx.currentTime);
    
    wowLfo.connect(wowLfoGain);
    wowLfoGain.connect(masterWowFlutterDelay.delayTime);
    wowLfo.start();
    
    flutterLfo = audioCtx.createOscillator();
    flutterLfo.type = "sine";
    flutterLfo.frequency.setValueAtTime(12.5, audioCtx.currentTime);
    
    flutterLfoGain = audioCtx.createGain();
    flutterLfoGain.gain.setValueAtTime(wowFlutterAmount * 0.0006, audioCtx.currentTime);
    
    flutterLfo.connect(flutterLfoGain);
    flutterLfoGain.connect(masterWowFlutterDelay.delayTime);
    flutterLfo.start();

    // Setup FX Chain
    setupFX();

    // Connect Lowpass -> Wow & Flutter master delay -> Analyser -> Master Gain -> Output
    lowpass.connect(masterWowFlutterDelay);
    masterWowFlutterDelay.connect(analyser);
    analyser.connect(masterGain);
    masterGain.connect(audioCtx.destination);
    
    // Procedural tape hiss/noise generator
    setupTapeNoise(lowpass);

    // Track Lowpass filter cutoff dynamically
    setInterval(() => {
        if (audioCtx && lowpass) {
            lowpass.frequency.setTargetAtTime(filterCutoff, audioCtx.currentTime, 0.1);
        }
    }, 100);

    return lowpass;
}

// Procedural Algorithmic Reverb
function setupFX() {
    // Delay Line
    const delay = audioCtx.createDelay(1.0);
    delay.delayTime.setValueAtTime(0.35, audioCtx.currentTime);
    
    const delayFeedback = audioCtx.createGain();
    delayFeedback.gain.setValueAtTime(0.4, audioCtx.currentTime);
    
    const delayMix = audioCtx.createGain();
    delayMix.gain.setValueAtTime(0.3, audioCtx.currentTime);
    
    // Auto-pan LFO for delay feedback to sweep left/right (ping-pong feeling)
    const delayPanner = audioCtx.createStereoPanner ? audioCtx.createStereoPanner() : null;
    if (delayPanner) {
        delayPanner.pan.setValueAtTime(0, audioCtx.currentTime);
        const delayLfo = audioCtx.createOscillator();
        const delayLfoGain = audioCtx.createGain();
        delayLfo.frequency.setValueAtTime(0.2, audioCtx.currentTime);
        delayLfoGain.gain.setValueAtTime(0.85, audioCtx.currentTime);
        delayLfo.connect(delayLfoGain);
        delayLfoGain.connect(delayPanner.pan);
        delayLfo.start();
        
        delay.connect(delayPanner);
        delayPanner.connect(delayFeedback);
    } else {
        delay.connect(delayFeedback);
    }
    
    delayFeedback.connect(delay); // feedback loop
    delay.connect(delayMix);
    
    delayNode = {
        delay: delay,
        gainNode: delayMix,
        feedback: delayFeedback
    };

    // Reverb: Algorithmic Feedback Comb Reverb
    const revInput = audioCtx.createGain();
    const revOutput = audioCtx.createGain();
    revOutput.gain.setValueAtTime(0.4, audioCtx.currentTime);

    const combTimes = [0.029, 0.037, 0.043, 0.051];
    combTimes.forEach(t => {
        const d = audioCtx.createDelay();
        d.delayTime.setValueAtTime(t, audioCtx.currentTime);
        const g = audioCtx.createGain();
        g.gain.setValueAtTime(0.78, audioCtx.currentTime);
        
        revInput.connect(d);
        d.connect(g);
        g.connect(d); // feedback
        g.connect(revOutput);
    });

    reverbNode = revOutput;
}

// Procedural Tape Noise & Crackle
function setupTapeNoise(destination) {
    const bufferSize = 2 * audioCtx.sampleRate;
    const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const output = noiseBuffer.getChannelData(0);
    
    for (let i = 0; i < bufferSize; i++) {
        let white = Math.random() * 2 - 1;
        let crackle = 0;
        
        if (Math.random() < 0.00008) {
            crackle = (Math.random() * 2 - 1) * 0.8;
        }
        
        output[i] = white * 0.05 + crackle;
    }
    
    const noise = audioCtx.createBufferSource();
    noise.buffer = noiseBuffer;
    noise.loop = true;
    
    const noiseFilter = audioCtx.createBiquadFilter();
    noiseFilter.type = "bandpass";
    noiseFilter.frequency.setValueAtTime(400, audioCtx.currentTime);
    noiseFilter.Q.setValueAtTime(0.7, audioCtx.currentTime);
    
    const noiseGain = audioCtx.createGain();
    noiseGain.gain.setValueAtTime(tapeWearAmount * 0.15, audioCtx.currentTime);
    
    noise.connect(noiseFilter);
    noiseFilter.connect(noiseGain);
    noiseGain.connect(destination);
    noise.start();

    noiseNode = {
        source: noise,
        gain: noiseGain
    };
}

// --- SYNTH GENERATORS WITH WOW & FLUTTER ---

function getWobblyFreq(baseFreq, stepOffset) {
    return baseFreq * Math.pow(2, stepOffset / 21);
}

function getScaleFreq(scaleDegree, octave) {
    const baseFreq = ROOT_FREQS[currentRoot] || 220.00;
    const scale = SCALES[currentScaleType];
    const degreeIndex = scaleDegree % scale.length;
    
    const octaveMultiplier = Math.floor(scaleDegree / scale.length) + (octave - 4);
    
    const stepOffset = scale[degreeIndex] + (21 * octaveMultiplier);
    return getWobblyFreq(baseFreq, stepOffset);
}

// 1. Soviet Detuned Pad
function triggerSovietPad(freqs, dest) {
    if (!enablePadCheckbox.checked) return;

    const oscs = [];
    const padGain = audioCtx.createGain();
    padGain.gain.setValueAtTime(0, audioCtx.currentTime);
    padGain.gain.linearRampToValueAtTime(0.20, audioCtx.currentTime + 1.0);
    
    freqs.forEach((freq, idx) => {
        const osc1 = audioCtx.createOscillator();
        const osc2 = audioCtx.createOscillator();
        
        osc1.type = idx % 2 === 0 ? "sawtooth" : "triangle";
        osc2.type = "sawtooth";
        
        osc1.frequency.setValueAtTime(freq - 1.2, audioCtx.currentTime);
        osc2.frequency.setValueAtTime(freq + 1.2, audioCtx.currentTime);
        
        osc1.connect(padGain);
        osc2.connect(padGain);
        
        osc1.start();
        osc2.start();
        
        oscs.push(osc1, osc2);
    });

    padGain.connect(dest);
    padGain.connect(reverbNode);

    return {
        stop: () => {
            const stopTime = audioCtx.currentTime + 2.5;
            padGain.gain.cancelScheduledValues(audioCtx.currentTime);
            padGain.gain.setValueAtTime(padGain.gain.value, audioCtx.currentTime);
            padGain.gain.linearRampToValueAtTime(0, stopTime);
            
            setTimeout(() => {
                oscs.forEach(osc => {
                    try { osc.stop(); } catch(e) {}
                });
            }, 3000);
        }
    };
}

// 2. Sport Pluck Synth
function triggerPluck(freq, dest) {
    if (!enablePluckCheckbox.checked) return;

    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();
    const filter = audioCtx.createBiquadFilter();

    osc.type = "square";
    osc.frequency.setValueAtTime(freq, audioCtx.currentTime);

    filter.type = "lowpass";
    filter.frequency.setValueAtTime(1500, audioCtx.currentTime);
    filter.frequency.exponentialRampToValueAtTime(150, audioCtx.currentTime + 0.3);

    gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.25, audioCtx.currentTime + 0.005);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 0.35);

    osc.connect(filter);
    filter.connect(gainNode);
    gainNode.connect(dest);

    gainNode.connect(delayNode.delay);
    gainNode.connect(reverbNode);

    osc.start();
    osc.stop(audioCtx.currentTime + 0.45);
}

// 3. FM Relic Glass Bell
function triggerFMBell(freq, dest) {
    if (!enableBellCheckbox.checked) return;

    const carrier = audioCtx.createOscillator();
    const modulator = audioCtx.createOscillator();
    const modGain = audioCtx.createGain();
    const gainNode = audioCtx.createGain();

    carrier.type = "sine";
    modulator.type = "sine";

    carrier.frequency.setValueAtTime(freq, audioCtx.currentTime);
    modulator.frequency.setValueAtTime(freq * 3.5, audioCtx.currentTime);

    modGain.gain.setValueAtTime(freq * 4, audioCtx.currentTime);
    modGain.gain.exponentialRampToValueAtTime(1, audioCtx.currentTime + 0.6);

    gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.15, audioCtx.currentTime + 0.002);
    gainNode.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.2);

    modulator.connect(modGain);
    modGain.connect(carrier.frequency);
    carrier.connect(gainNode);
    gainNode.connect(dest);

    gainNode.connect(delayNode.delay);
    gainNode.connect(reverbNode);

    modulator.start();
    carrier.start();

    modulator.stop(audioCtx.currentTime + 1.3);
    carrier.stop(audioCtx.currentTime + 1.3);
}

// 4. Vocoder Trumpet
function triggerTrumpet(freq, dest) {
    if (!enableTrumpet) return;

    const osc1 = audioCtx.createOscillator();
    const osc2 = audioCtx.createOscillator();
    const vibrato = audioCtx.createOscillator();
    const vibratoGain = audioCtx.createGain();
    
    osc1.type = "sawtooth";
    osc2.type = "sawtooth";
    
    osc1.frequency.setValueAtTime(freq * 0.98, audioCtx.currentTime);
    osc2.frequency.setValueAtTime(freq * 1.02, audioCtx.currentTime);
    
    vibrato.frequency.setValueAtTime(6.8, audioCtx.currentTime);
    vibratoGain.gain.setValueAtTime(20, audioCtx.currentTime);
    vibrato.connect(vibratoGain);
    vibratoGain.connect(osc1.frequency);
    vibratoGain.connect(osc2.frequency);
    
    const mainGain = audioCtx.createGain();
    mainGain.gain.setValueAtTime(0, audioCtx.currentTime);
    mainGain.gain.linearRampToValueAtTime(0.2, audioCtx.currentTime + 0.08);
    mainGain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + 1.1);
    
    const filter1 = audioCtx.createBiquadFilter();
    const filter2 = audioCtx.createBiquadFilter();
    const filter3 = audioCtx.createBiquadFilter();
    
    filter1.type = "bandpass";
    filter2.type = "bandpass";
    filter3.type = "bandpass";
    
    filter1.frequency.setValueAtTime(650, audioCtx.currentTime);
    filter1.Q.setValueAtTime(10, audioCtx.currentTime);
    
    filter2.frequency.setValueAtTime(1050, audioCtx.currentTime);
    filter2.Q.setValueAtTime(10, audioCtx.currentTime);
    
    filter3.frequency.setValueAtTime(2200, audioCtx.currentTime);
    filter3.Q.setValueAtTime(8, audioCtx.currentTime);
    
    osc1.connect(filter1);
    osc1.connect(filter2);
    osc1.connect(filter3);
    
    osc2.connect(filter1);
    osc2.connect(filter2);
    osc2.connect(filter3);
    
    const filterMix = audioCtx.createGain();
    filter1.connect(filterMix);
    filter2.connect(filterMix);
    filter3.connect(filterMix);
    
    const crunchOsc = audioCtx.createOscillator();
    const crunchGain = audioCtx.createGain();
    crunchOsc.frequency.setValueAtTime(130, audioCtx.currentTime);
    crunchOsc.type = "sawtooth";
    
    const ringMod = audioCtx.createGain();
    ringMod.gain.setValueAtTime(0.4, audioCtx.currentTime);
    
    crunchOsc.connect(crunchGain);
    crunchGain.connect(ringMod.gain);
    
    filterMix.connect(ringMod);
    ringMod.connect(mainGain);
    
    mainGain.connect(dest);
    mainGain.connect(delayNode.delay);
    mainGain.connect(reverbNode);
    
    osc1.start();
    osc2.start();
    vibrato.start();
    crunchOsc.start();
    
    const stopTime = audioCtx.currentTime + 1.2;
    osc1.stop(stopTime);
    osc2.stop(stopTime);
    vibrato.stop(stopTime);
    crunchOsc.stop(stopTime);
}

// 5. Happy Theremin
let lastThereminFreq = 440;
function triggerTheremin(freq, dest) {
    if (!enableTheremin) return;
    
    const osc = audioCtx.createOscillator();
    const vibrato = audioCtx.createOscillator();
    const vibratoGain = audioCtx.createGain();
    const gainNode = audioCtx.createGain();
    
    osc.type = "triangle";
    
    const startFreq = lastThereminFreq;
    lastThereminFreq = freq;
    
    osc.frequency.setValueAtTime(startFreq, audioCtx.currentTime);
    osc.frequency.exponentialRampToValueAtTime(freq, audioCtx.currentTime + 0.18);
    
    vibrato.frequency.setValueAtTime(6.2, audioCtx.currentTime);
    vibratoGain.gain.setValueAtTime(30, audioCtx.currentTime);
    
    vibrato.connect(vibratoGain);
    vibratoGain.connect(osc.frequency);
    
    gainNode.gain.setValueAtTime(0, audioCtx.currentTime);
    gainNode.gain.linearRampToValueAtTime(0.12, audioCtx.currentTime + 0.08);
    gainNode.gain.setTargetAtTime(0, audioCtx.currentTime + 0.08, 0.3);
    
    osc.connect(gainNode);
    gainNode.connect(dest);
    
    gainNode.connect(delayNode.delay);
    gainNode.connect(reverbNode);
    
    osc.start();
    vibrato.start();
    
    const stopTime = audioCtx.currentTime + 1.7;
    osc.stop(stopTime);
    vibrato.stop(stopTime);
}

// 6. Sad Guitar
function triggerGuitar(freq, dest) {
    if (!enableGuitar) return;
    
    const delayTime = 1 / freq;
    const noiseLength = 0.025;
    const bufferSize = audioCtx.sampleRate * noiseLength;
    const noiseBuffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const data = noiseBuffer.getChannelData(0);
    
    for (let i = 0; i < bufferSize; i++) {
        data[i] = (Math.random() * 2 - 1) * Math.exp(-5 * i / bufferSize);
    }
    
    const noiseSource = audioCtx.createBufferSource();
    noiseSource.buffer = noiseBuffer;
    
    const noiseGain = audioCtx.createGain();
    noiseGain.gain.setValueAtTime(0.25, audioCtx.currentTime);
    
    const delay = audioCtx.createDelay(1.0);
    delay.delayTime.setValueAtTime(delayTime, audioCtx.currentTime);
    
    const feedback = audioCtx.createGain();
    feedback.gain.setValueAtTime(0.985, audioCtx.currentTime);
    
    const dampFilter = audioCtx.createBiquadFilter();
    dampFilter.type = "lowpass";
    dampFilter.frequency.setValueAtTime(1800, audioCtx.currentTime);
    
    noiseSource.connect(noiseGain);
    noiseGain.connect(delay);
    
    delay.connect(dampFilter);
    dampFilter.connect(feedback);
    feedback.connect(delay);
    
    const outputGain = audioCtx.createGain();
    outputGain.gain.setValueAtTime(1.0, audioCtx.currentTime);
    outputGain.gain.setTargetAtTime(0, audioCtx.currentTime, 0.35);
    
    dampFilter.connect(outputGain);
    outputGain.connect(dest);
    
    outputGain.connect(delayNode.delay);
    outputGain.connect(reverbNode);
    
    noiseSource.start();
    
    setTimeout(() => {
        try {
            noiseSource.stop();
            noiseSource.disconnect();
            noiseGain.disconnect();
            delay.disconnect();
            dampFilter.disconnect();
            feedback.disconnect();
            outputGain.disconnect();
        } catch(e) {}
    }, 2200);
}

// 7. Interactive Drums Synthesis
function triggerKick(time) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const gain = audioCtx.createGain();
    osc.connect(gain);
    gain.connect(lowpassNode || audioCtx.destination);
    
    osc.frequency.setValueAtTime(150, time);
    osc.frequency.exponentialRampToValueAtTime(0.01, time + 0.15);
    
    gain.gain.setValueAtTime(0.5, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + 0.15);
    
    osc.start(time);
    osc.stop(time + 0.16);
}

function triggerSnare(time) {
    if (!audioCtx) return;
    const bufferSize = audioCtx.sampleRate * 0.15;
    const buffer = audioCtx.createBuffer(1, bufferSize, audioCtx.sampleRate);
    const data = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
        data[i] = Math.random() * 2 - 1;
    }
    
    const noise = audioCtx.createBufferSource();
    noise.buffer = buffer;
    
    const filter = audioCtx.createBiquadFilter();
    filter.type = "bandpass";
    filter.frequency.value = 1000;
    
    const gain = audioCtx.createGain();
    
    noise.connect(filter);
    filter.connect(gain);
    gain.connect(lowpassNode || audioCtx.destination);
    
    gain.gain.setValueAtTime(0.3, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + 0.15);
    
    noise.start(time);
    noise.stop(time + 0.16);
}

function triggerHiHat(time) {
    if (!audioCtx) return;
    const osc = audioCtx.createOscillator();
    const filter = audioCtx.createBiquadFilter();
    const gain = audioCtx.createGain();
    
    osc.type = "triangle";
    osc.frequency.value = 10000;
    
    filter.type = "highpass";
    filter.frequency.value = 7000;
    
    osc.connect(filter);
    filter.connect(gain);
    gain.connect(lowpassNode || audioCtx.destination);
    
    gain.gain.setValueAtTime(0.15, time);
    gain.gain.exponentialRampToValueAtTime(0.01, time + 0.05);
    
    osc.start(time);
    osc.stop(time + 0.06);
}

function startDrumSequencer() {
    if (drumIntervalId) clearInterval(drumIntervalId);
    
    const tickTimeMs = (60000 / currentBpm) / 4;
    drumIntervalId = setInterval(() => {
        if (!isPlaying || !enableDrums || !audioCtx) return;
        
        const time = audioCtx.currentTime;
        const beat = drumTickCount % 16;
        
        if (beat === 0 || beat === 8) {
            triggerKick(time);
        } else if (beat === 4 || beat === 12) {
            triggerSnare(time);
            triggerKick(time);
        }
        
        if (beat % 2 === 0) {
            triggerHiHat(time);
        }
        
        drumTickCount++;
    }, tickTimeMs);
}

// --- SEQUENCER & CHORD AUTOMATOR ---
let activePadNotes = null;
let currentPad = null;

function updatePadChord(dest) {
    if (!isPlaying) return;
    
    const scale = SCALES[currentScaleType];
    const baseFreq = ROOT_FREQS[currentRoot] || 220.00;
    const isMinor = currentScaleType.includes("minor") || currentScaleType.includes("dorian") || currentScaleType.includes("phrygian");
    const prog = isMinor ? PROGRESSIONS.minor : PROGRESSIONS.major;
    
    const chordOffsets = prog[activeChordIdx];
    activeChordIdx = (activeChordIdx + 1) % prog.length;
    
    const chordFreqs = chordOffsets.map(offset => {
        const degree = scale[offset % scale.length];
        const totalSteps = degree + 21 * -1;
        return getWobblyFreq(baseFreq, totalSteps);
    });

    if (currentPad) {
        currentPad.stop();
    }
    
    currentPad = triggerSovietPad(chordFreqs, dest);
    activePadNotes = chordOffsets;
}

// --- GRAVITATIONAL SOUNDBOX (PHYSICS CANVAS) ---

class SoundNode {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.vx = (Math.random() - 0.5) * 5;
        this.vy = (Math.random() - 0.5) * 5;
        this.radius = 12 + Math.random() * 8;
        
        this.scaleDegree = Math.floor(Math.random() * 10);
        this.lastTriggerTime = 0;
        this.trail = [];

        const types = ["pluck", "bell", "trumpet", "theremin", "guitar"];
        this.instrumentType = types[Math.floor(Math.random() * types.length)];
        
        if (this.instrumentType === "pluck") {
            this.color = "rgba(229, 178, 43, 0.75)";
            this.trailColor = "rgba(229, 178, 43, 0.1)";
        } else if (this.instrumentType === "bell") {
            this.color = "rgba(0, 200, 255, 0.75)";
            this.trailColor = "rgba(0, 200, 255, 0.1)";
        } else if (this.instrumentType === "trumpet") {
            this.color = "rgba(255, 68, 68, 0.75)";
            this.trailColor = "rgba(255, 68, 68, 0.1)";
        } else if (this.instrumentType === "theremin") {
            this.color = "rgba(100, 255, 100, 0.75)";
            this.trailColor = "rgba(100, 255, 100, 0.1)";
        } else {
            this.color = "rgba(200, 100, 255, 0.75)";
            this.trailColor = "rgba(200, 100, 255, 0.1)";
        }

        this.normalCanvas = null;
        this.triggeredCanvas = null;
        this.prerender();
    }

    prerender() {
        const size = Math.ceil((this.radius + 4) * 2);
        const center = size / 2;

        this.normalCanvas = document.createElement("canvas");
        this.normalCanvas.width = size;
        this.normalCanvas.height = size;
        const ctxN = this.normalCanvas.getContext("2d");

        this.triggeredCanvas = document.createElement("canvas");
        this.triggeredCanvas.width = size;
        this.triggeredCanvas.height = size;
        const ctxT = this.triggeredCanvas.getContext("2d");

        const style = getComputedStyle(document.documentElement || document.body);
        const borderColor = style.getPropertyValue('--border-color').trim() || "#2B3BE5";
        const short = this.instrumentType.substring(0, 2).toUpperCase();

        // Draw Normal State
        ctxN.beginPath();
        ctxN.arc(center, center, this.radius, 0, Math.PI * 2);
        ctxN.fillStyle = this.color;
        ctxN.strokeStyle = borderColor;
        ctxN.lineWidth = 2;
        ctxN.fill();
        ctxN.stroke();

        ctxN.fillStyle = "#000000";
        ctxN.font = "8px monospace";
        ctxN.textAlign = "center";
        ctxN.textBaseline = "middle";
        ctxN.fillText(`${short}-${this.scaleDegree}`, center, center);

        // Draw Triggered State
        ctxT.beginPath();
        ctxT.arc(center, center, this.radius, 0, Math.PI * 2);
        ctxT.fillStyle = "rgba(255, 255, 255, 0.95)";
        ctxT.strokeStyle = "#D11919";
        ctxT.lineWidth = 2;
        ctxT.fill();
        ctxT.stroke();

        ctxT.fillStyle = "#000000";
        ctxT.font = "8px monospace";
        ctxT.textAlign = "center";
        ctxT.textBaseline = "middle";
        ctxT.fillText(`${short}-${this.scaleDegree}`, center, center);
    }

    update() {
        this.vy += GRAVITY;
        this.vx *= FRICTION;
        this.vy *= FRICTION;

        this.x += this.vx;
        this.y += this.vy;

        this.trail.push({x: this.x, y: this.y});
        if (this.trail.length > 8) {
            this.trail.shift();
        }
    }

    draw(ctx) {
        this.trail.forEach((p, idx) => {
            ctx.beginPath();
            ctx.arc(p.x, p.y, this.radius * (idx / this.trail.length), 0, Math.PI * 2);
            ctx.fillStyle = this.trailColor;
            ctx.fill();
        });

        const isTriggered = Date.now() - this.lastTriggerTime < 150;
        const sourceCanvas = isTriggered ? this.triggeredCanvas : this.normalCanvas;
        if (sourceCanvas) {
            const offset = sourceCanvas.width / 2;
            ctx.drawImage(sourceCanvas, this.x - offset, this.y - offset);
        }
    }

    bounceCheck(width, height, dest) {
        let bounced = false;
        
        if (this.x - this.radius < 0) {
            this.x = this.radius;
            this.vx = -this.vx * 0.95;
            bounced = true;
        } else if (this.x + this.radius > width) {
            this.x = width - this.radius;
            this.vx = -this.vx * 0.95;
            bounced = true;
        }

        if (this.y - this.radius < 0) {
            this.y = this.radius;
            this.vy = -this.vy * 0.95;
            bounced = true;
        } else if (this.y + this.radius > height) {
            this.y = height - this.radius;
            this.vy = -this.vy * 0.95;
            bounced = true;
        }

        if (bounced && isPlaying && dest) {
            this.lastTriggerTime = Date.now();
            
            let targetDegree = this.scaleDegree;
            if (activePadNotes && Math.random() < 0.7) {
                const padOffset = activePadNotes[Math.floor(Math.random() * activePadNotes.length)];
                targetDegree = padOffset + (Math.random() < 0.5 ? 0 : 5);
            }

            const freq = getScaleFreq(targetDegree, 4);
            const highFreq = getScaleFreq(targetDegree, 5);
            const subFreq = getScaleFreq(targetDegree, 3);
            
            if (this.instrumentType === "pluck") {
                triggerPluck(freq, dest);
            } else if (this.instrumentType === "bell") {
                triggerFMBell(highFreq, dest);
            } else if (this.instrumentType === "trumpet") {
                triggerTrumpet(subFreq, dest);
            } else if (this.instrumentType === "theremin") {
                triggerTheremin(highFreq, dest);
            } else if (this.instrumentType === "guitar") {
                triggerGuitar(freq, dest);
            }
        }
    }
}

// Init Canvas dimensions
function resizeCanvases() {
    if (sandboxCanvas.parentElement) {
        sandboxCanvas.width = sandboxCanvas.parentElement.clientWidth;
        sandboxCanvas.height = 300;
    }
    if (visualizerCanvas.parentElement) {
        visualizerCanvas.width = visualizerCanvas.parentElement.clientWidth;
        visualizerCanvas.height = 100;
    }
}

window.addEventListener("resize", resizeCanvases);
resizeCanvases();

// Tap canvas to add node
sandboxCanvas.addEventListener("click", (e) => {
    const rect = sandboxCanvas.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    if (balls.length < 15) {
        balls.push(new SoundNode(x, y));
    }
});

// Setup default nodes
function seedNodes() {
    balls = [];
    const w = sandboxCanvas.width || 400;
    const h = sandboxCanvas.height || 300;
    for (let i = 0; i < 6; i++) {
        balls.push(new SoundNode(w * 0.2 + w * 0.15 * i, h * 0.3 + Math.random() * h * 0.2));
    }
}
seedNodes();

// Reels animation toggling
function startReelsAnimation() {
    if (leftReel) leftReel.classList.add("spinning");
    if (rightReel) rightReel.classList.add("spinning");
}

function stopReelsAnimation() {
    if (leftReel) leftReel.classList.remove("spinning", "spinning-fast", "spinning-reverse-fast");
    if (rightReel) rightReel.classList.remove("spinning", "spinning-fast", "spinning-reverse-fast");
}

function updateCounterDisplay() {
    const hrs = String(Math.floor(tapeCounterSecs / 3600)).padStart(2, '0');
    const mins = String(Math.floor((tapeCounterSecs % 3600) / 60)).padStart(2, '0');
    const secs = String(tapeCounterSecs % 60).padStart(2, '0');
    if (tapeCounter) tapeCounter.textContent = `${hrs}:${mins}:${secs}`;
}

// Tape control deck listeners
const rewBtn = document.getElementById("rew-btn");
const ffBtn = document.getElementById("ff-btn");
const ejectBtn = document.getElementById("eject-btn");
const playerPlayBtn = document.getElementById("player-play-btn");

if (rewBtn) {
    rewBtn.addEventListener("click", () => {
        if (!leftReel) return;
        leftReel.classList.add("spinning-reverse-fast");
        rightReel.classList.add("spinning-reverse-fast");
        leftReel.classList.remove("spinning", "spinning-fast");
        rightReel.classList.remove("spinning", "spinning-fast");
        
        trackingText.textContent = "REWIND TAPE...";
        statusText.textContent = "DECODER REWIND";
        
        let count = 0;
        const interval = setInterval(() => {
            if (tapeCounterSecs > 0) {
                tapeCounterSecs = Math.max(0, tapeCounterSecs - 8);
                updateCounterDisplay();
            }
            count++;
            if (count > 15 || tapeCounterSecs === 0) {
                clearInterval(interval);
                restoreReelsAfterAction();
            }
        }, 100);
    });
}

if (ffBtn) {
    ffBtn.addEventListener("click", () => {
        if (!leftReel) return;
        leftReel.classList.add("spinning-fast");
        rightReel.classList.add("spinning-fast");
        leftReel.classList.remove("spinning", "spinning-reverse-fast");
        rightReel.classList.remove("spinning", "spinning-reverse-fast");
        
        trackingText.textContent = "FAST FORWARD...";
        statusText.textContent = "DECODER FF";
        
        let count = 0;
        const interval = setInterval(() => {
            tapeCounterSecs += 8;
            updateCounterDisplay();
            count++;
            if (count > 15) {
                clearInterval(interval);
                restoreReelsAfterAction();
            }
        }, 100);
    });
}

if (ejectBtn) {
    ejectBtn.addEventListener("click", () => {
        balls = [];
        if (isPlaying) {
            playBtn.click();
        }
        if (leftReel) {
            leftReel.classList.add("spinning-fast");
            rightReel.classList.add("spinning-fast");
        }
        statusText.textContent = "TAPE EJECTED // АРХИВ";
        trackingText.textContent = "NO TAPE INSIDE";
        tapeCounterSecs = 0;
        updateCounterDisplay();
        
        setTimeout(() => {
            stopReelsAnimation();
        }, 600);
    });
}

function restoreReelsAfterAction() {
    if (isPlaying) {
        startReelsAnimation();
        trackingText.textContent = "PLAYING • SYSTEM OK";
        statusText.textContent = "DECODER SYSTEM ACTIVE // 1989-REAL";
    } else {
        stopReelsAnimation();
        trackingText.textContent = "TAPE PAUSED";
        statusText.textContent = "SYSTEM STANDBY";
    }
}

// Master Gain Volume Control scrubber interaction
const volumeBar = document.querySelector(".volume-slider-bar");
const volumeProgress = document.querySelector(".volume-progress");
if (volumeBar && volumeProgress) {
    volumeBar.addEventListener("click", (e) => {
        const rect = volumeBar.getBoundingClientRect();
        const percent = Math.min(1, Math.max(0, (e.clientX - rect.left) / rect.width));
        volumeProgress.style.width = `${percent * 100}%`;
        if (masterGain && audioCtx) {
            masterGain.gain.setTargetAtTime(percent * 0.8, audioCtx.currentTime, 0.05);
        }
    });
}

// --- ANIMATION / DSP PROCESSING LOOPS ---

let lowpassNode = null;

function animate() {
    ctxSandbox.fillStyle = "#090807";
    ctxSandbox.fillRect(0, 0, sandboxCanvas.width, sandboxCanvas.height);

    if (Math.random() < 0.03) {
        ctxSandbox.fillStyle = "rgba(229, 178, 43, 0.05)";
        ctxSandbox.fillRect(0, Math.random() * sandboxCanvas.height, sandboxCanvas.width, 4);
    }

    balls.forEach(ball => {
        ball.update();
        ball.bounceCheck(sandboxCanvas.width, sandboxCanvas.height, lowpassNode);
        ball.draw(ctxSandbox);
    });

    ctxVisualizer.fillStyle = "#070605";
    ctxVisualizer.fillRect(0, 0, visualizerCanvas.width, visualizerCanvas.height);

    if (isPlaying) {
        if (analyser) {
            analyser.getByteTimeDomainData(dataArray);
            
            ctxVisualizer.lineWidth = 2;
            ctxVisualizer.strokeStyle = "#00FF66";
            ctxVisualizer.shadowBlur = 4;
            ctxVisualizer.shadowColor = "#00FF66";
            
            ctxVisualizer.beginPath();
            const sliceWidth = visualizerCanvas.width / analyser.frequencyBinCount;
            let x = 0;
            
            for (let i = 0; i < analyser.frequencyBinCount; i++) {
                const v = dataArray[i] / 128.0;
                const y = v * visualizerCanvas.height / 2;
                
                if (i === 0) {
                    ctxVisualizer.moveTo(x, y);
                } else {
                    ctxVisualizer.lineTo(x, y);
                }
                x += sliceWidth;
            }
            ctxVisualizer.lineTo(visualizerCanvas.width, visualizerCanvas.height / 2);
            ctxVisualizer.stroke();
            ctxVisualizer.shadowBlur = 0;
        } else {
            // Draw premium simulated glowing analog scope wave before user gesture
            ctxVisualizer.lineWidth = 2;
            ctxVisualizer.strokeStyle = "#00FF66";
            ctxVisualizer.shadowBlur = 4;
            ctxVisualizer.shadowColor = "#00FF66";
            ctxVisualizer.beginPath();
            
            const time = Date.now() * 0.006;
            const sliceWidth = 2;
            const count = visualizerCanvas.width / sliceWidth;
            
            for (let i = 0; i < count; i++) {
                const x = i * sliceWidth;
                const wave1 = Math.sin(i * 0.08 + time) * 16;
                const wave2 = Math.sin(i * 0.04 - time * 1.3) * 8;
                const noise = (Math.random() - 0.5) * 3;
                const y = (visualizerCanvas.height / 2) + wave1 + wave2 + noise;
                
                if (i === 0) {
                    ctxVisualizer.moveTo(x, y);
                } else {
                    ctxVisualizer.lineTo(x, y);
                }
            }
            ctxVisualizer.stroke();
            ctxVisualizer.shadowBlur = 0;
        }

        if (Math.random() < 0.02) {
            ctxVisualizer.fillStyle = "rgba(209, 25, 25, 0.25)";
            ctxVisualizer.fillRect(0, Math.random() * visualizerCanvas.height, visualizerCanvas.width, 2);
        }
    } else {
        ctxVisualizer.lineWidth = 1;
        ctxVisualizer.strokeStyle = "rgba(229, 178, 43, 0.3)";
        ctxVisualizer.beginPath();
        ctxVisualizer.moveTo(0, visualizerCanvas.height / 2);
        ctxVisualizer.lineTo(visualizerCanvas.width, visualizerCanvas.height / 2);
        ctxVisualizer.stroke();
    }

    // VHS Timestamp update
    if (isPlaying) {
        const time = Date.now() - lastProgressTime;
        if (time > 1000) {
            tapeCounterSecs++;
            lastProgressTime = Date.now();
            updateCounterDisplay();
            
            // Progress Bar playhead sync (assuming 120s loop)
            const playheadProgress = document.getElementById("playhead-progress");
            if (playheadProgress) {
                const percent = (tapeCounterSecs % 120) / 120 * 100;
                playheadProgress.style.width = `${percent}%`;
            }
        }
    }

    requestAnimationFrame(animate);
}

// Start/Stop engine toggle
playBtn.addEventListener("click", () => {
    if (!isPlaying) {
        if (!audioCtx) {
            autoStartAudio();
            return;
        }
        
        if (audioCtx.state === "suspended") {
            audioCtx.resume();
        }
        
        isPlaying = true;
        playBtn.textContent = "STOP TAPE / СТОП";
        playBtn.style.background = "#E5B22B";
        playBtn.style.boxShadow = "0 4px 0px #A0740A, 0 6px 10px rgba(0,0,0,0.6)";
        
        if (playerPlayBtn) playerPlayBtn.textContent = "⏸";
        
        statusText.textContent = "DECODER SYSTEM ACTIVE // 1989-REAL";
        pulseDot.classList.add("active");
        trackingText.textContent = "PLAYING • SYSTEM OK";
        
        lastProgressTime = Date.now();
        startReelsAnimation();

        // Start Ambient Pad Chord Loops
        updatePadChord(lowpassNode);
        padIntervalId = setInterval(() => {
            updatePadChord(lowpassNode);
        }, (60 / currentBpm) * 4000);

        // Start Drum sequencer if active
        if (enableDrums) {
            startDrumSequencer();
        }
        
    } else {
        if (!audioCtx) {
            isPlaying = false;
            playBtn.textContent = "START TAPE / ПУСК";
            playBtn.style.background = "var(--accent)";
            playBtn.style.boxShadow = "0 4px 0px #700B0B, 0 6px 10px rgba(0,0,0,0.6)";
            if (playerPlayBtn) playerPlayBtn.textContent = "▶";
            statusText.textContent = "SYSTEM STANDBY";
            pulseDot.classList.remove("active");
            trackingText.textContent = "TAPE PAUSED";
            stopReelsAnimation();
            return;
        }
        
        isPlaying = false;
        playBtn.textContent = "START TAPE / ПУСК";
        playBtn.style.background = "var(--accent)";
        playBtn.style.boxShadow = "0 4px 0px #700B0B, 0 6px 10px rgba(0,0,0,0.6)";
        
        if (playerPlayBtn) playerPlayBtn.textContent = "▶";
        
        statusText.textContent = "SYSTEM STANDBY";
        pulseDot.classList.remove("active");
        trackingText.textContent = "TAPE PAUSED";
        stopReelsAnimation();

        if (currentPad) {
            currentPad.stop();
            currentPad = null;
        }
        clearInterval(padIntervalId);
        if (drumIntervalId) {
            clearInterval(drumIntervalId);
            drumIntervalId = null;
        }
        
        if (audioCtx) {
            audioCtx.suspend();
        }
    }
});

if (playerPlayBtn) {
    playerPlayBtn.addEventListener("click", () => {
        playBtn.click();
    });
}

// Auto-unlock Web Audio context on first user gesture
function autoStartAudio() {
    if (isPlaying && !audioCtx) {
        lowpassNode = initAudio();
        if (delayNode && delayNode.gainNode) {
            delayNode.gainNode.connect(lowpassNode);
        }
        if (reverbNode) {
            reverbNode.connect(lowpassNode);
        }
        
        // Start Ambient Pad Chord Loops
        updatePadChord(lowpassNode);
        padIntervalId = setInterval(() => {
            updatePadChord(lowpassNode);
        }, (60 / currentBpm) * 4000);

        // Start Drum sequencer if active
        if (enableDrums) {
            startDrumSequencer();
        }
    }
    // Remove gesture listeners to prevent double initialization
    document.removeEventListener("click", autoStartAudio);
    document.removeEventListener("keydown", autoStartAudio);
}

// Add user gesture audio activation listeners
document.addEventListener("click", autoStartAudio);
document.addEventListener("keydown", autoStartAudio);

// Kick off animation rendering
requestAnimationFrame(animate);
updateSliderValues();

// Start page in active visualizer mode by default
lastProgressTime = Date.now();
startReelsAnimation();
if (pulseDot) pulseDot.classList.add("active");
if (playBtn) {
    playBtn.textContent = "STOP TAPE / СТОП";
    playBtn.style.background = "#E5B22B";
    playBtn.style.boxShadow = "0 4px 0px #A0740A, 0 6px 10px rgba(0,0,0,0.6)";
}
if (playerPlayBtn) playerPlayBtn.textContent = "⏸";
if (statusText) statusText.textContent = "DECODER SYSTEM ACTIVE // 1989-REAL";
if (trackingText) trackingText.textContent = "PLAYING • SYSTEM OK";

