const fs = require('fs');
const path = require('path');
const googleTTS = require('google-tts-api');
const https = require('https');

const data = [
  { id: '1_frase', text: "Concepto: Frase nunca escrita antes. ¿Puede una IA generarlo? Sí, probablemente. ¿Queda probado automáticamente? No implica valor ni verdad." },
  { id: '2_hipotesis', text: "Concepto: Hipótesis nueva. ¿Puede una IA generarlo? Sí. ¿Queda probado automáticamente? No implica que sea correcta." },
  { id: '3_deduccion', text: "Concepto: Deducción matemática. ¿Puede una IA generarlo? Sí. ¿Queda probado automáticamente? Requiere demostración verificable." },
  { id: '4_descubrimiento', text: "Concepto: Descubrimiento científico. ¿Puede una IA generarlo? Puede proponerlo. ¿Queda probado automáticamente? Requiere experimento o datos." },
  { id: '5_hecho', text: "Concepto: Hecho que ningún humano conoce. ¿Puede una IA generarlo? No puede garantizarlo. ¿Queda probado automáticamente? Requiere una condición imposible de verificar globalmente." }
];

const publicDir = path.join(__dirname, '../public/audio');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

async function generate() {
  console.log('Iniciando generación de audios...');
  for (const item of data) {
    const url = googleTTS.getAudioUrl(item.text, {
      lang: 'es',
      slow: false,
      host: 'https://translate.google.com',
    });
    console.log(`Downloading ${item.id}.mp3...`);
    const filePath = path.join(publicDir, `${item.id}.mp3`);
    await new Promise((resolve, reject) => {
      https.get(url, (res) => {
        const fileStream = fs.createWriteStream(filePath);
        res.pipe(fileStream);
        fileStream.on('finish', resolve);
      }).on('error', reject);
    });
  }
  console.log('Voces generadas.');
}

generate();
