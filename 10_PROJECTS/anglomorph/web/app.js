// CONFIGURACIÓN DE CONJUNTOS DE CARACTERES
const CONSONANTS = "bdfghjklmnprstvwz";
const VOWELS = "aeiou";
const SYLLABLES = [];
for (let c of CONSONANTS) {
    for (let v of VOWELS) {
        SYLLABLES.push(c + v);
    }
}
const SYLLABLE_SET = new Set(SYLLABLES);
const ENGLISH_ALPHABET = "abcdefghijklmnopqrstuvwxyz";

// ARITMÉTICA BIYECTIVA (BigInt para evitar pérdida de precisión)
function engToInt(word) {
    const k = BigInt(ENGLISH_ALPHABET.length);
    let val = 0n;
    const wordLower = word.toLowerCase();
    for (let i = 0; i < wordLower.length; i++) {
        const idx = ENGLISH_ALPHABET.indexOf(wordLower[i]);
        if (idx !== -1) {
            val = val * k + BigInt(idx + 1);
        }
    }
    return val;
}

function intToEng(n) {
    const k = BigInt(ENGLISH_ALPHABET.length);
    let s = [];
    let temp = BigInt(n);
    while (temp > 0n) {
        temp -= 1n;
        s.push(ENGLISH_ALPHABET[Number(temp % k)]);
        temp /= k;
    }
    return s.reverse().join("");
}

function intToAng(n) {
    const k = BigInt(SYLLABLES.length);
    let s = [];
    let temp = BigInt(n);
    while (temp > 0n) {
        temp -= 1n;
        s.push(SYLLABLES[Number(temp % k)]);
        temp /= k;
    }
    return s.reverse().join("");
}

function angToInt(word) {
    const wordLower = word.toLowerCase();
    const k = BigInt(SYLLABLES.length);
    let val = 0n;
    for (let i = 0; i < wordLower.length; i += 2) {
        const chunk = wordLower.slice(i, i + 2);
        const idx = SYLLABLES.indexOf(chunk);
        val = val * k + BigInt(idx + 1);
    }
    return val;
}

// FORMATO Y CASE PRESERVATION
function preserveCase(source, target) {
    if (source === source.toUpperCase() && source !== source.toLowerCase()) {
        return target.toUpperCase();
    }
    if (source.length > 0 && source[0] === source[0].toUpperCase() && source[0] !== source[0].toLowerCase()) {
        return target.charAt(0).toUpperCase() + target.slice(1).toLowerCase();
    }
    return target.toLowerCase();
}

function isValidEnglishWord(word) {
    return /^[a-zA-Z]+$/.test(word);
}

function isValidAnglomorphWord(word) {
    if (!/^[a-zA-Z]+$/.test(word)) return false;
    if (word.length % 2 !== 0) return false;
    const wordLower = word.toLowerCase();
    for (let i = 0; i < wordLower.length; i += 2) {
        if (!SYLLABLE_SET.has(wordLower.slice(i, i + 2))) {
            return false;
        }
    }
    return true;
}

function translateWordToAng(word) {
    if (!isValidEnglishWord(word)) return word;
    const n = engToInt(word);
    const ang = intToAng(n);
    return preserveCase(word, ang);
}

function translateWordToEng(word) {
    if (!isValidAnglomorphWord(word)) return word;
    const n = angToInt(word);
    const eng = intToEng(n);
    return preserveCase(word, eng);
}

function translateText(text, toAnglomorph = true) {
    const tokens = text.match(/[a-zA-Z]+|[^a-zA-Z]+/g) || [];
    const result = [];
    for (let token of tokens) {
        if (toAnglomorph) {
            result.push(translateWordToAng(token));
        } else {
            result.push(translateWordToEng(token));
        }
    }
    return result.join("");
}

// CONTROLADORES DE LA INTERFAZ
const textLeft = document.getElementById("text-left");
const textRight = document.getElementById("text-right");
const labelLeft = document.getElementById("label-left");
const labelRight = document.getElementById("label-right");
const btnSwap = document.getElementById("btn-swap");
const btnClearLeft = document.getElementById("btn-clear-left");
const btnCopyRight = document.getElementById("btn-copy-right");

const consensusStatus = document.getElementById("consensus-status");
const entropyValue = document.getElementById("entropy-value");
const distortionValue = document.getElementById("distortion-value");

let toAnglomorphMode = true;

function calculateEntropy(str) {
    if (!str) return "0.00";
    const len = str.length;
    const freqs = {};
    for (let i = 0; i < len; i++) {
        const char = str[i];
        freqs[char] = (freqs[char] || 0) + 1;
    }
    let entropy = 0;
    for (const char in freqs) {
        const p = freqs[char] / len;
        entropy -= p * Math.log2(p);
    }
    return entropy.toFixed(2);
}

function updateMetrics() {
    const valLeft = textLeft.value;
    const valRight = textRight.value;
    
    // 1. Entropía de Shannon del texto origen
    entropyValue.textContent = calculateEntropy(valLeft);
    
    // 2. Tasa de Distorsión
    if (valLeft.length === 0) {
        distortionValue.textContent = "0.00%";
    } else {
        const dist = ((valRight.length - valLeft.length) / valLeft.length) * 100;
        distortionValue.textContent = (dist >= 0 ? "+" : "") + dist.toFixed(2) + "%";
    }
    
    // 3. Consenso BFT Local (Verificación de Biyección Inversa)
    if (!valLeft.trim()) {
        consensusStatus.textContent = "STABLE";
        consensusStatus.className = "metric-value text-green";
        return;
    }
    
    const retranslated = translateText(valRight, !toAnglomorphMode);
    if (retranslated === valLeft) {
        consensusStatus.textContent = "STABLE";
        consensusStatus.className = "metric-value text-green";
    } else {
        consensusStatus.textContent = "DEGRADED";
        consensusStatus.className = "metric-value";
        consensusStatus.style.color = "#FF453A"; // iOS Red
    }
}

function processTranslation() {
    const val = textLeft.value;
    textRight.value = translateText(val, toAnglomorphMode);
    updateMetrics();
}

textLeft.addEventListener("input", processTranslation);

btnSwap.addEventListener("click", () => {
    toAnglomorphMode = !toAnglomorphMode;
    
    // Intercambiar etiquetas
    if (toAnglomorphMode) {
        labelLeft.textContent = "INGLÉS (V)";
        labelRight.textContent = "ANGLOMORPH (W)";
        textLeft.placeholder = "Escribe o pega texto en inglés aquí...";
    } else {
        labelLeft.textContent = "ANGLOMORPH (W)";
        labelRight.textContent = "INGLÉS (V)";
        textLeft.placeholder = "Escribe o pega texto en Anglomorph aquí...";
    }
    
    // Intercambiar contenido de los textareas
    const temp = textLeft.value;
    textLeft.value = textRight.value;
    textRight.value = temp;
    
    processTranslation();
});

btnClearLeft.addEventListener("click", () => {
    textLeft.value = "";
    textRight.value = "";
    updateMetrics();
});

btnCopyRight.addEventListener("click", () => {
    if (textRight.value) {
        navigator.clipboard.writeText(textRight.value);
        const originalText = btnCopyRight.textContent;
        btnCopyRight.textContent = "¡Copiado!";
        setTimeout(() => {
            btnCopyRight.textContent = originalText;
        }, 1500);
    }
});
