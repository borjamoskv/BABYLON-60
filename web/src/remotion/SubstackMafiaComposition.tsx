import React from 'react';
import { Composition, AbsoluteFill, useCurrentFrame, interpolate, spring, useVideoConfig } from 'remotion';

export interface MafiaNode {
  id: string;
  label: string;
  isReciprocal: boolean;
  x: number;
  y: number;
}

// 64 Nodos OSINT extraídos de la investigación "Substack Mafia"
const OSINT_NODES: MafiaNode[] = Array.from({ length: 64 }, (_, i) => ({
  id: `node_${i + 1}`,
  label: i === 0 ? 'David (Humo Gurú)' : i < 5 ? `Pacto Recíproco ${i}` : `Nodo ${i + 1}`,
  isReciprocal: i < 42,
  x: 200 + (Math.sin(i * 0.3) * 600) + 700,
  y: 200 + (Math.cos(i * 0.3) * 350) + 400,
}));

// ESCENA 1: El Grafo del Engaño
export const SubstackMafiaGraphScene: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const nodeScale = spring({ frame, fps, config: { damping: 12 } });
  const rotation = interpolate(frame, [0, 600], [0, 360]);

  return (
    <AbsoluteFill style={{ backgroundColor: '#0f172a', color: '#fff', fontFamily: 'monospace' }}>
      <div style={{ position: 'absolute', top: 40, left: 60, zIndex: 10 }}>
        <h1 style={{ color: '#ef4444', fontSize: '3rem', margin: 0 }}>
          LA SUBSTACK MAFIA EN ESPAÑOL
        </h1>
        <p style={{ color: '#94a3b8', fontSize: '1.5rem', marginTop: '8px' }}>
          Análisis Forense C5-REAL: 64 Nodos | 828 Enlaces | 42 Pactos Recíprocos
        </p>
      </div>

      <svg style={{ width: '100%', height: '100%', position: 'absolute' }}>
        {OSINT_NODES.map((nodeA, idxA) =>
          OSINT_NODES.slice(idxA + 1).map((nodeB) => {
            const isReciprocal = nodeA.isReciprocal && nodeB.isReciprocal;
            const strokeColor = isReciprocal ? 'rgba(239, 68, 68, 0.6)' : 'rgba(148, 163, 184, 0.15)';
            const strokeWidth = isReciprocal ? 2.5 : 1;

            return (
              <line
                key={`edge_${nodeA.id}_${nodeB.id}`}
                x1={nodeA.x}
                y1={nodeA.y}
                x2={nodeB.x}
                y2={nodeB.y}
                stroke={strokeColor}
                strokeWidth={strokeWidth}
              />
            );
          })
        )}
      </svg>

      {OSINT_NODES.map((node) => (
        <div
          key={node.id}
          style={{
            position: 'absolute',
            left: node.x,
            top: node.y,
            transform: `translate(-50%, -50%) scale(${nodeScale}) rotate(${node.isReciprocal ? rotation * 0.1 : 0}deg)`,
            backgroundColor: node.id === 'node_1' ? '#f59e0b' : node.isReciprocal ? '#ef4444' : '#3b82f6',
            color: '#ffffff',
            padding: '8px 14px',
            borderRadius: '20px',
            boxShadow: node.isReciprocal ? '0 0 15px rgba(239, 68, 68, 0.8)' : 'none',
            fontSize: '12px',
            fontWeight: 'bold',
            border: node.isReciprocal ? '2px solid #f87171' : 'none',
          }}
        >
          {node.label}
        </div>
      ))}
    </AbsoluteFill>
  );
};

// ESCENA 2: La Guillotina del Paywall
export const PaywallGuillotineScene: React.FC = () => {
  const frame = useCurrentFrame();
  const blurAmount = interpolate(frame, [0, 45], [0, 16], { extrapolateRight: 'clamp' });
  const modalY = interpolate(frame, [0, 45], [100, 0], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill style={{ backgroundColor: '#fffbe6', color: '#1c1917', fontFamily: 'Georgia, serif', padding: '60px' }}>
      {/* Texto de lectura cortado */}
      <div style={{ opacity: Math.max(0.2, 1 - (blurAmount / 16)), maxWidth: '800px', margin: '0 auto' }}>
        <h1 style={{ fontSize: '3rem', marginBottom: '20px' }}>El Secreto Último de la Atención Soberana</h1>
        <p style={{ fontSize: '1.5rem', lineHeight: 1.8 }}>
          En este capítulo revelamos cómo los algoritmos de condicionamiento operante convierten el acto sagrado de la lectura en un mercado estocástico de clics. La verdad sobre la conciencia es que...
        </p>
      </div>

      {/* Modal de Paywall esmerilado */}
      <div
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `translate(-50%, -50%) translateY(${modalY}px)`,
          width: '650px',
          padding: '40px',
          borderRadius: '24px',
          background: 'rgba(255, 255, 255, 0.95)',
          boxShadow: '0 20px 50px rgba(0,0,0,0.25)',
          border: '1px solid rgba(251, 191, 36, 0.5)',
          textAlign: 'center',
        }}
      >
        <div style={{ fontSize: '4rem', marginBottom: '10px' }}>🔒</div>
        <h2 style={{ fontSize: '2rem', color: '#78350f', margin: '10px 0' }}>CONTENIDO EXCLUSIVO PARA MIEMBROS</h2>
        <p style={{ fontSize: '1.2rem', color: '#92400e', marginBottom: '24px' }}>
          Desbloquea el resto de este artículo y accede al Chat Privado por solo 500$/año.
        </p>
        <button
          style={{
            backgroundColor: '#d97706',
            color: '#fff',
            border: 'none',
            padding: '16px 36px',
            fontSize: '1.2rem',
            fontWeight: 'bold',
            borderRadius: '12px',
            cursor: 'pointer',
            boxShadow: '0 4px 15px rgba(217, 119, 6, 0.4)',
          }}
        >
          Unirme a la Casa (Tier Fundador)
        </button>
      </div>
    </AbsoluteFill>
  );
};

// ESCENA 3: Farándula POP Trapped
export const PopStarCameoScene: React.FC = () => {
  const frame = useCurrentFrame();
  const shake = Math.sin(frame * 0.5) * 5;

  return (
    <AbsoluteFill style={{ backgroundColor: '#09090b', color: '#f4f4f5', padding: '60px', fontFamily: 'monospace' }}>
      <h1 style={{ color: '#ec4899', fontSize: '2.5rem', textAlign: 'center' }}>
        EPISODIO II: LAS CELEBRIDADES EN EL GRAFO
      </h1>

      <div style={{ display: 'flex', justifyContent: 'center', gap: '40px', marginTop: '80px', flexWrap: 'wrap' }}>
        {/* El Xokas Card */}
        <div style={{ width: '320px', background: '#18181b', padding: '24px', borderRadius: '16px', border: '1px solid #ef4444', transform: `translateY(${shake}px)` }}>
          <h3 style={{ color: '#f87171' }}>El Xokas</h3>
          <p style={{ fontSize: '14px', color: '#a1a1aa' }}>"¡ESTO NO ES UN JUEGO, CHAVAL! ¡O PAGAS LA SUSCRIPCIÓN O TE VAS A LA P*TA CALLE, MANDA CARALLO!"</p>
          <span style={{ fontSize: '12px', color: '#ef4444' }}>Status: Atrapadiño en el Pacto #14</span>
        </div>

        {/* Sócrates Card */}
        <div style={{ width: '320px', background: '#18181b', padding: '24px', borderRadius: '16px', border: '1px solid #eab308', transform: `translateY(${-shake}px)` }}>
          <h3 style={{ color: '#facc15' }}>Sócrates</h3>
          <p style={{ fontSize: '14px', color: '#a1a1aa' }}>"Solo sé que no sé nada... a menos que entres a mi Substack Premium por 50 dracmas."</p>
          <span style={{ fontSize: '12px', color: '#ef4444' }}>Status: Atrapado en el Pacto #01</span>
        </div>

        {/* Chiquitócres Card */}
        <div style={{ width: '320px', background: '#18181b', padding: '24px', borderRadius: '16px', border: '1px solid #10b981', transform: `translateY(${shake}px)` }}>
          <h3 style={{ color: '#34d399' }}>Chiquitócres</h3>
          <p style={{ fontSize: '14px', color: '#a1a1aa' }}>"¿Te das cuén, Platón? ¡Por la gloria de mi madre, la caverna es un paywall, fistro pecador!"</p>
          <span style={{ fontSize: '12px', color: '#ef4444' }}>Status: Atrapado en el Pacto #22</span>
        </div>

        {/* Sergio UTBH Card */}
        <div style={{ width: '320px', background: '#18181b', padding: '24px', borderRadius: '16px', border: '1px solid #3b82f6', transform: `translateY(${-shake}px)` }}>
          <h3 style={{ color: '#60a5fa' }}>Sergio (UTBH)</h3>
          <p style={{ fontSize: '14px', color: '#a1a1aa' }}>"Hola a todos. Hoy desgranamos cómo el feminismo algorítmico oprime al macho alfa empotrador, carallo. ¡Todo es culpa de la guagua matriarcal, bro!"</p>
          <span style={{ fontSize: '12px', color: '#ef4444' }}>Status: Atrapado en el Pacto #33</span>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ESCENA 4: Crítica de la Razón Mafiosa (Kant x Remotion)
export const CritiqueOfMafiosoReasonScene: React.FC = () => {
  const frame = useCurrentFrame();

  const opacity = interpolate(frame, [0, 45], [0, 1], { extrapolateRight: 'clamp' });
  const translateY = interpolate(frame, [0, 45], [50, 0], { extrapolateRight: 'clamp' });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: '#1e1e2e',
        color: '#cdd6f4',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '80px',
        fontFamily: 'Georgia, serif',
      }}
    >
      <div style={{ opacity, transform: `translateY(${translateY}px)`, textAlign: 'center', maxWidth: '1000px' }}>
        <h2 style={{ fontSize: '3.5rem', color: '#f38ba8', marginBottom: '24px' }}>
          CRÍTICA DE LA RAZÓN MAFIOSA
        </h2>
        <blockquote style={{ fontSize: '2rem', fontStyle: 'italic', lineHeight: 1.5, color: '#bac2de' }}>
          "Dos cosas llenan el ánimo de admiración y silencio: la inmensidad del ciberespacio frente a mí y la codicia del pacto de recomendación recíproca debajo de mí."
        </blockquote>
        <p style={{ marginTop: '40px', fontSize: '1.4rem', color: '#a6adc8', fontFamily: 'monospace' }}>
          — Investigaciones OSINT C5-REAL | Telmo Dinámico de Moskv
        </p>
      </div>
    </AbsoluteFill>
  );
};

// COMPOSICIÓN PRINCIPAL
export const RemotionVideoRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="SubstackMafiaGraph"
        component={SubstackMafiaGraphScene}
        durationInFrames={1800}
        fps={60}
        width={1920}
        height={1080}
      />
      <Composition
        id="PaywallGuillotine"
        component={PaywallGuillotineScene}
        durationInFrames={1200}
        fps={60}
        width={1920}
        height={1080}
      />
      <Composition
        id="PopStarCameos"
        component={PopStarCameoScene}
        durationInFrames={1200}
        fps={60}
        width={1920}
        height={1080}
      />
      <Composition
        id="CritiqueOfMafiosoReason"
        component={CritiqueOfMafiosoReasonScene}
        durationInFrames={1200}
        fps={60}
        width={1920}
        height={1080}
      />
    </>
  );
};
