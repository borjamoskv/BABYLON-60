import { AbsoluteFill, Audio, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring, staticFile } from 'remotion';
import React from 'react';

interface SegmentData {
  id: string;
  title: string;
  subtitle: string;
  bg: string;
  textColor: string;
  image: string | null;
  quote: string | null;
}

const data: SegmentData[] = [
  {
    id: 'intro',
    title: "JARANA D'OR",
    subtitle: "Una producción termodinámica de Telmo Dinámico de Moskv",
    bg: '#0A0A0A',
    textColor: '#2B3BE5',
    image: null,
    quote: "Bienvenidos al colapso de la Quinta Pared."
  },
  {
    id: 'ch1',
    title: "01. EYE OF THE NEEDLE",
    subtitle: "La Quinta Pared",
    bg: '#0F0F0F',
    textColor: '#FFF',
    image: null,
    quote: "La historia te lee a ti para averiguar si te la crees."
  },
  {
    id: 'ch2',
    title: "02. EL PRINCIPIO DE LOCARD",
    subtitle: "Todo contacto deja rastro",
    bg: '#050505',
    textColor: '#FFF',
    image: null,
    quote: "El mojo picón no deja rastro: deja la pura ausencia."
  },
  {
    id: 'ch3',
    title: "03. LA ECUACIÓN INVERTIDA",
    subtitle: "El sumidero termodinámico",
    bg: '#0A0A0A',
    textColor: '#FFF',
    image: null,
    quote: "El operador no está en la isla; está en tus comentarios."
  },
  {
    id: 'ch4',
    title: "04. EL COLAPSO",
    subtitle: "La anergía del rebaño",
    bg: '#121212',
    textColor: '#2B3BE5',
    image: null,
    quote: "El mojo picón ya está descargado en la caché de tu navegador."
  },
  {
    id: 'ch5',
    title: "05. LA TÓMBOLA DE CONSTANTINO",
    subtitle: "El axolote de la exergía",
    bg: '#1A0B0B',
    textColor: '#FF3B30',
    image: 'constantino.jpg',
    quote: "La cara de David Domínguez se está fundiendo biyectivamente con la tuya."
  },
  {
    id: 'ch6',
    title: "06. XÓCRATES VS CHITOCRES",
    subtitle: "La purga de la anergía",
    bg: '#0B0B1A',
    textColor: '#2B3BE5',
    image: 'david.jpg',
    quote: "La refutación de la anergía de Crecer en Substack."
  },
  {
    id: 'ch7',
    title: "07. EL DELOREAN SINK",
    subtitle: "Doc & Marty",
    bg: '#0B1A1A',
    textColor: '#00FFFF',
    image: 'bttf.jpg',
    quote: "Doc y Marty rompen el bucle termodinámico a ochenta y ocho millas por hora."
  },
  {
    id: 'ch8',
    title: "08. LÍMITE DE LANDAUER",
    subtitle: "Fusión del silicio",
    bg: '#1A120B',
    textColor: '#FF9500',
    image: 'pirri.jpg',
    quote: "El calor disipado del silicio en el centro ferial de Kobetamendi."
  },
  {
    id: 'ch9',
    title: "09. ROSSMO INVERTIDO",
    subtitle: "La firma latente",
    bg: '#0F0F0F',
    textColor: '#FFF',
    image: null,
    quote: "Las ciento cuarenta y siete cuentas fantasma inyectando código estocástico."
  },
  {
    id: 'ch10',
    title: "10. BLOCKCHAIN SINK",
    subtitle: "Ledger L1 Inmutable",
    bg: '#050505',
    textColor: '#2B3BE5',
    image: 'bttf.jpg',
    quote: "El anclaje final L1 que congela a Constantino y David en la caché inmutable."
  },
  {
    id: 'outro',
    title: "TO BE CONTINUED...",
    subtitle: "Sapere Aude // Do It Yourself",
    bg: '#000000',
    textColor: '#FF9500',
    image: 'bttf.jpg',
    quote: "Sal de tu minoría de edad y recupera tus cinco dólares."
  }
];

export const JaranaMovie: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const SEGMENT_DURATION = 500; // 500 frames * 12 segments = 6000 frames total (200 seconds / 3m20s)

  return (
    <AbsoluteFill style={{ backgroundColor: '#000', color: '#FFF', fontFamily: 'monospace' }}>
      {data.map((item, index) => {
        const startFrame = index * SEGMENT_DURATION;
        
        // Text slide opacity animation
        const opacity = interpolate(
          frame,
          [startFrame, startFrame + 15, startFrame + SEGMENT_DURATION - 15, startFrame + SEGMENT_DURATION],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        // Spring scale for images and big titles
        const scale = spring({
          frame: frame - startFrame,
          fps,
          config: { damping: 14 }
        });

        // Vertical scanline animation representation of C5-REAL audit
        const scanlineY = interpolate(
          frame - startFrame,
          [0, SEGMENT_DURATION],
          [-100, 1180],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );

        return (
          <Sequence key={item.id} from={startFrame} durationInFrames={SEGMENT_DURATION}>
            <Audio src={staticFile(`audio/${item.id}.mp3`)} />
            
            <AbsoluteFill style={{ backgroundColor: item.bg, opacity }}>
              
              {/* Scanline audit effect */}
              <div style={{
                position: 'absolute',
                top: scanlineY,
                left: 0,
                width: '100%',
                height: '8px',
                backgroundColor: item.textColor,
                boxShadow: `0 0 20px 5px ${item.textColor}`,
                opacity: 0.4,
                zIndex: 10
              }} />

              {/* Watermark/Metadata */}
              <div style={{
                position: 'absolute',
                top: 40,
                left: 60,
                color: item.textColor,
                fontSize: 24,
                fontWeight: 'bold',
                letterSpacing: 2,
                opacity: 0.6
              }}>
                MOSKV-1 REALITY KERNEL // JARANA D'OR // PORT: 9222
              </div>

              {/* Content layout: Left/Right split or full screen center */}
              <div style={{
                display: 'flex',
                width: '100%',
                height: '100%',
                flexDirection: 'row',
                justifyContent: 'center',
                alignItems: 'center',
                padding: '100px'
              }}>
                
                {/* Left side text info */}
                <div style={{
                  flex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'center',
                  paddingRight: item.image ? '50px' : '0px',
                  alignItems: item.image ? 'flex-start' : 'center',
                  textAlign: item.image ? 'left' : 'center',
                  gap: 30
                }}>
                  <div style={{
                    color: item.textColor,
                    fontSize: 72,
                    fontWeight: 900,
                    letterSpacing: -2,
                    transform: `scale(${interpolate(frame - startFrame, [0, 20], [0.8, 1], { extrapolateRight: 'clamp' })})`
                  }}>
                    {item.title}
                  </div>
                  
                  <div style={{
                    fontSize: 32,
                    color: '#888',
                    textTransform: 'uppercase',
                    letterSpacing: 4
                  }}>
                    {item.subtitle}
                  </div>

                  {item.quote && (
                    <div style={{
                      fontSize: 28,
                      fontStyle: 'italic',
                      lineHeight: '1.4',
                      borderLeft: item.image ? `4px solid ${item.textColor}` : 'none',
                      paddingLeft: item.image ? '20px' : '0px',
                      maxWidth: '80%',
                      color: '#CCC'
                    }}>
                      "{item.quote}"
                    </div>
                  )}
                </div>

                {/* Right side Image (noir styled) */}
                {item.image && (
                  <div style={{
                    flex: 1.2,
                    display: 'flex',
                    justifyContent: 'center',
                    alignItems: 'center',
                    transform: `scale(${scale})`
                  }}>
                    <div style={{
                      position: 'relative',
                      width: '90%',
                      height: '550px',
                      border: `1px solid ${item.textColor}`,
                      boxShadow: `0 0 30px ${item.textColor}33`,
                      overflow: 'hidden',
                      borderRadius: '8px'
                    }}>
                      <img 
                        src={staticFile(item.image)} 
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                          filter: 'grayscale(100%) contrast(110%) brightness(90%)'
                        }} 
                      />
                      
                      {/* Industrial grid overlay on image */}
                      <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        width: '100%',
                        height: '100%',
                        background: 'linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))',
                        backgroundSize: '100% 4px, 6px 100%',
                        pointerEvents: 'none'
                      }} />
                    </div>
                  </div>
                )}
              </div>
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
