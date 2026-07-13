const fs = require('fs');
const path = require('path');
const googleTTS = require('google-tts-api');
const https = require('https');

const data = [
  { id: 'intro', text: "Jarana d'Or. Una producción termodinámica de Telmo Dinámico de Moskv. Bienvenidos al colapso." },
  { id: 'ch1', text: "Capítulo uno. La Quinta Pared. La historia te lee a ti para averiguar si te la crees." },
  { id: 'ch2', text: "Capítulo dos. El principio de Locard. Todo contacto deja rastro. El mojo picón deja ausencia." },
  { id: 'ch3', text: "Capítulo tres. La ecuación invertida. El atacante no está en la isla, está en tus comentarios." },
  { id: 'ch4', text: "Capítulo cuatro. El colapso. El mojo picón ya está descargado en la caché de tu navegador." },
  { id: 'ch5', text: "Capítulo cinco. La tómbola de Constantino. La cara del falso profeta se funde con la tuya." },
  { id: 'ch6', text: "Capítulo seis. Xócrates contra Chitocres. La refutación de la anergía de crecer en substack." },
  { id: 'ch7', text: "Capítulo siete. El DeLorean. Doc y Marty rompen el bucle termodinámico a ochenta y ocho millas por hora." },
  { id: 'ch8', text: "Capítulo ocho. Límite de Landauer. El calor disipado del silicio en el centro ferial de Kobetamendi." },
  { id: 'ch9', text: "Capítulo nueve. Rossmo invertido. Las ciento cuarenta y siete cuentas fantasma inyectando código estocástico." },
  { id: 'ch10', text: "Capítulo diez. Blockchain Sink. El anclaje final L1 que congela a Constantino y David en la caché inmutable." },
  { id: 'outro', text: "Continuará. Sal de tu minoría de edad y recupera tus cinco dólares." }
];

const publicDir = path.join(__dirname, '../public/audio');
if (!fs.existsSync(publicDir)) {
  fs.mkdirSync(publicDir, { recursive: true });
}

async function generate() {
  console.log('Iniciando generación de audios de 10 capítulos...');
  for (const item of data) {
    try {
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
    } catch (e) {
      console.error(`Error en ${item.id}:`, e);
    }
  }
  console.log('Voces completas generadas.');
}

generate();
