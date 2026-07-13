import { AbsoluteFill, Audio, Sequence, useCurrentFrame, useVideoConfig, interpolate, spring, staticFile } from 'remotion';

const data = [
  { id: '1_frase', concepto: "Frase nunca escrita antes", gen: "Sí, probablemente", prueba: "No implica valor ni verdad" },
  { id: '2_hipotesis', concepto: "Hipótesis nueva", gen: "Sí", prueba: "No implica que sea correcta" },
  { id: '3_deduccion', concepto: "Deducción matemática", gen: "Sí", prueba: "Requiere demostración verificable" },
  { id: '4_descubrimiento', concepto: "Descubrimiento científico", gen: "Puede proponerlo", prueba: "Requiere experimento o datos" },
  { id: '5_hecho', concepto: "Hecho que ningún humano conoce", gen: "No puede garantizarlo", prueba: "Requiere una condición imposible de verificar globalmente" }
];

export const EpistemicLimits: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  
  // Each segment will be 350 frames
  const SEGMENT_DURATION = 350;

  return (
    <AbsoluteFill style={{ backgroundColor: '#0A0A0A', fontFamily: 'monospace', color: '#FFF' }}>
      <div style={{ position: 'absolute', top: 50, left: 50, color: '#2B3BE5', fontSize: 30, fontWeight: 'bold' }}>
        MOSKV-1 APEX // LIMITES EPISTÉMICOS
      </div>
      
      {data.map((item, index) => {
        const startFrame = index * SEGMENT_DURATION;
        const textOpacity = interpolate(
          frame,
          [startFrame, startFrame + 15, startFrame + SEGMENT_DURATION - 15, startFrame + SEGMENT_DURATION],
          [0, 1, 1, 0],
          { extrapolateLeft: 'clamp', extrapolateRight: 'clamp' }
        );
        
        const scale = spring({
          frame: frame - startFrame,
          fps,
          config: { damping: 12 }
        });

        return (
          <Sequence key={item.id} from={startFrame} durationInFrames={SEGMENT_DURATION}>
            <Audio src={staticFile(`audio/${item.id}.mp3`)} />
            <AbsoluteFill style={{ justifyContent: 'center', alignItems: 'center', opacity: textOpacity }}>
              <div style={{ transform: `scale(${scale})`, display: 'flex', flexDirection: 'column', gap: 40, width: '80%' }}>
                
                <div style={{ borderLeft: '10px solid #2B3BE5', paddingLeft: 40 }}>
                  <div style={{ fontSize: 40, color: '#888' }}>CONCEPTO</div>
                  <div style={{ fontSize: 80, fontWeight: 'bold' }}>{item.concepto}</div>
                </div>

                <div style={{ borderLeft: '10px solid #FFF', paddingLeft: 40 }}>
                  <div style={{ fontSize: 40, color: '#888' }}>¿PUEDE UNA IA GENERARLO?</div>
                  <div style={{ fontSize: 60 }}>{item.gen}</div>
                </div>

                <div style={{ borderLeft: '10px solid #2B3BE5', paddingLeft: 40 }}>
                  <div style={{ fontSize: 40, color: '#888' }}>¿QUEDA PROBADO AUTOMÁTICAMENTE?</div>
                  <div style={{ fontSize: 60, color: '#2B3BE5' }}>{item.prueba}</div>
                </div>

              </div>
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
