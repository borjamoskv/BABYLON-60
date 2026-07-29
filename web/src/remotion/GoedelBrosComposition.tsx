import React from 'react';
import { AbsoluteFill, Composition, useCurrentFrame, Audio, staticFile, Sequence, Loop } from 'remotion';

// Fuentes genéricas monoespaciadas para forzar el look 8-bit sin dependencias externas
const PIXEL_FONT = '"Courier New", Courier, monospace';

const CharacterCard: React.FC<{
  name: string;
  role: string;
  dialogue: string;
  color: string;
}> = ({ name, role, dialogue, color }) => {
  const frame = useCurrentFrame();

  // Efecto máquina de escribir (más rápido y robótico)
  const visibleCharacters = Math.max(0, Math.floor(frame / 2));
  const currentText = dialogue.substring(0, visibleCharacters);
  
  // Parpadeo del cursor (1 o 0)
  const showCursor = Math.floor(frame / 15) % 2 === 0;
  
  // Calcular cuánto dura el efecto de escritura para cortar el sonido del "blip"
  const typingDurationFrames = dialogue.length * 2;

  return (
    <>
      {/* Sistema de sonido estilo RPG 8-bits */}
      <Sequence from={0} durationInFrames={typingDurationFrames}>
        <Loop durationInFrames={3}>
          <Audio src={staticFile('audio/blip.wav')} volume={0.15} />
        </Loop>
      </Sequence>

      <div style={{
        backgroundColor: '#000000',
        border: `4px solid ${color}`,
        padding: '20px',
        display: 'flex',
        flexDirection: 'column',
        // Sombra dura sólida de 8-bits
        boxShadow: `8px 8px 0px 0px ${color}`,
        position: 'relative',
        fontFamily: PIXEL_FONT,
        textTransform: 'uppercase',
        width: '100%',
        height: '100%',
        boxSizing: 'border-box'
      }}>
        
        <div style={{ display: 'flex', alignItems: 'flex-start', marginBottom: '20px', borderBottom: `2px dashed ${color}`, paddingBottom: '10px' }}>
          <div style={{ 
            width: '48px', height: '48px', 
            backgroundColor: color,
            display: 'flex', justifyContent: 'center', alignItems: 'center',
            fontSize: '24px', fontWeight: 'bold', color: '#000',
            marginRight: '20px',
            border: '2px solid #fff' // Borde cuadrado
          }}>
            {name.charAt(0)}
          </div>
          <div>
            <h2 style={{ margin: 0, color: '#ffffff', fontSize: '1.4rem', fontWeight: 'bold' }}>{name}</h2>
            <span style={{ color: color, fontSize: '0.8rem', letterSpacing: '1px' }}>LVL 99 - {role}</span>
          </div>
        </div>
        
        <div style={{ flex: 1 }}>
          <p style={{ 
            margin: 0, 
            color: '#32cd32', // Verde terminal clásico
            fontSize: '1.1rem', 
            lineHeight: 1.4,
            fontWeight: 'bold',
            textShadow: '2px 2px 0px #000'
          }}>
            {currentText}{showCursor && visibleCharacters < dialogue.length ? '█' : ''}
          </p>
        </div>
      </div>
    </>
  );
};

export const GoedelBrosScene: React.FC = () => {
  return (
    <AbsoluteFill style={{ 
      backgroundColor: '#000080', // Azul clásico de MS-DOS o Crash de Windows
      padding: '40px',
      fontFamily: PIXEL_FONT,
      display: 'flex',
      flexDirection: 'column'
    }}>
      <div style={{ textAlign: 'center', marginBottom: '30px', border: '4px solid #fff', backgroundColor: '#000', padding: '15px', boxShadow: '8px 8px 0px 0px #fff', zIndex: 10 }}>
        <h1 style={{ color: '#ffff00', fontSize: '2.5rem', margin: '0 0 10px 0', textTransform: 'uppercase' }}>
          * SELECT YOUR CHARACTER *
        </h1>
        <p style={{ color: '#fff', fontSize: '1.2rem', margin: 0 }}>
          PRESS START TO HACK THE SALES FUNNEL
        </p>
      </div>

      <div style={{ 
        display: 'grid', 
        gridTemplateColumns: '1fr 1fr', 
        gridTemplateRows: '1fr 1fr', 
        gap: '30px',
        flex: 1,
        position: 'relative',
        zIndex: 10
      }}>
        {/* Gödel */}
        <div style={{ position: 'relative' }}>
          <Sequence from={30}>
            <CharacterCard
              name="KURT GÖDEL"
              role="ARCHITECT"
              color="#00ffff"
              dialogue="AIBA LA HOSTIA, BRO. TU SISTEMA DE CAPTACION DE LEADS NO PUEDE DEMOSTRAR SU PROPIO ROI DESDE DENTRO. NECESITAS UN AXIOMA EXTERNO PARA QUE EL CHIRINGUITO NO SEA INCONSISTENTE. ¡FUNNELS CIRCULARES!"
            />
          </Sequence>
        </div>

        {/* Turing */}
        <div style={{ position: 'relative' }}>
          <Sequence from={240}>
            <CharacterCard
              name="ALAN TURING"
              role="HACKER"
              color="#ff00ff"
              dialogue="ILLO, ESCUCHAME. HE MONTAO UNA MAQUINA UNIVERSAL Y TE DIGO QUE EL PROBLEMA DE LA PARADA ES TU TASA DE REBOTE. EL ALGORITMO SE QUEDA COLGAO. ¡QUE NO COMPUTA, PICHA, QUE NO COMPUTA!"
            />
          </Sequence>
        </div>

        {/* Cantor */}
        <div style={{ position: 'relative' }}>
          <Sequence from={450}>
            <CharacterCard
              name="GEORG CANTOR"
              role="SCALER"
              color="#00ff00"
              dialogue="¡ALEPH-SUB-CERO LEADS! SI METES UN INFINITO NO NUMERABLE EN LA PARTE ALTA DEL FUNNEL, LA CONVERSION EN LA DIAGONAL COLAPSA TU STRIPE. ESTAIS PENSANDO MUY PEQUEÑO."
            />
          </Sequence>
        </div>

        {/* El Xokas */}
        <div style={{ position: 'relative' }}>
          <Sequence from={660}>
            <CharacterCard
              name="EL XOKAS"
              role="BOSS"
              color="#ff0000"
              dialogue="PERO VAMOS A VER. ¿QUE COJONES ME ESTAIS CONTANDO DE AXIOMAS? SI NO HACEIS DIRECTOS DE 14 HORAS PICANDO PIEDRA, NO VAIS A VENDER NADA. ¡MENOS TEOREMAS Y MAS CURRAR, NPCs DE LA LOGICA!"
            />
          </Sequence>
        </div>
      </div>

      {/* OVERLAY CRT SCANLINES Y VIÑETA */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0, bottom: 0,
        pointerEvents: 'none',
        zIndex: 100,
        background: `
          linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.25) 50%), 
          linear-gradient(90deg, rgba(255, 0, 0, 0.06), rgba(0, 255, 0, 0.02), rgba(0, 0, 255, 0.06))
        `,
        backgroundSize: '100% 4px, 3px 100%',
        boxShadow: 'inset 0 0 100px rgba(0,0,0,0.9)'
      }} />
      
    </AbsoluteFill>
  );
};

export const GoedelBrosRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="GoedelBrosMasterclass"
        component={GoedelBrosScene}
        durationInFrames={1200}
        fps={60}
        width={1920}
        height={1080}
      />
    </>
  );
};
