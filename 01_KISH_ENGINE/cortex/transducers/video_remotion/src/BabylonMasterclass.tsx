import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate, Series } from "remotion";

export type MotionPhysics = {
  mass: number;
  damping: number;
  stiffness: number;
};

export type SceneData = {
  durationInFrames: number;
  text: string;
  phaseId: number;
  phaseTitle: string;
  physics: MotionPhysics;
};

const PHASE_COLORS: Record<number, { accent: string; glow: string; border: string; formula: string; formulaDesc: string }> = {
  1: { 
    accent: "#00F0DC", 
    glow: "rgba(0, 240, 220, 0.4)", 
    border: "rgba(0, 240, 220, 0.5)",
    formula: "H = -\\sum_{i} \\lambda_i \\ln \\lambda_i \\quad [\\text{Hamiltoniano de Atención}]",
    formulaDesc: "POSTULADO: EL GRAFO DE ATENCIÓN COLAPSA EN UN ESTADO DE EQUILIBRIO"
  },
  2: { 
    accent: "#FFB428", 
    glow: "rgba(255, 180, 40, 0.4)", 
    border: "rgba(255, 180, 40, 0.5)",
    formula: "\\nabla \\cdot J_{\\text{softmax}} \\neq 0 \\implies \\Delta S_{\\text{irreversible}} > 0",
    formulaDesc: "ANOMALÍA: EL SOFTMAX NO ES HERMITIANO; QUIEBRA EL BALANCE DETALLADO"
  },
  3: { 
    accent: "#FF4444", 
    glow: "rgba(255, 68, 68, 0.5)", 
    border: "rgba(255, 68, 68, 0.6)",
    formula: "\\delta \\mathcal{H}_{\\text{null}} \\perp \\text{Truth} \\implies \\text{COLAPSO POR FALSIFICACIÓN}",
    formulaDesc: "PRUEBA POPPERIANA: PERTURBACIÓN EN SUBESPACIO NULO DESTRUYE EL MAPA"
  },
};

// ==============================================================================
// COMPONENTE: VISUALIZADOR DE ONDA Y GRAFO ESPECTRAL DINÁMICO
// ==============================================================================
const KineticSpectrumVisualizer: React.FC<{ phaseId: number; frame: number; accent: string }> = ({ phaseId, frame, accent }) => {
  const bars = 42;
  return (
    <div style={{ display: "flex", alignItems: "flex-end", gap: "6px", height: "48px", width: "100%" }}>
      {Array.from({ length: bars }).map((_, i) => {
        // Simulación de espectro FFT dinámico armónico
        const freq1 = Math.sin((frame * 0.15) + (i * 0.45));
        const freq2 = Math.cos((frame * 0.08) - (i * 0.25));
        const chaos = phaseId === 2 ? Math.sin(frame * 0.8 + i) * 0.4 : 0; // Fricción térmica caótica en fase 2
        const rawHeight = Math.abs(freq1 * 0.6 + freq2 * 0.4 + chaos);
        const barHeight = Math.max(12, Math.min(48, rawHeight * 48));
        
        return (
          <div
            key={i}
            style={{
              flex: 1,
              height: `${barHeight}px`,
              backgroundColor: i % 2 === 0 ? accent : `${accent}99`,
              borderRadius: "2px",
              boxShadow: `0 0 8px ${accent}66`,
              transition: "height 0.05s ease",
            }}
          />
        );
      })}
    </div>
  );
};

// ==============================================================================
// COMPONENTE: RED CUÁNTICA / GRAFO DE ATENCIÓN PROCEDURAL
// ==============================================================================
const QuantumLatticeGraphic: React.FC<{ phaseId: number; frame: number; accent: string }> = ({ phaseId, frame, accent }) => {
  const nodeCount = 8;
  const radius = 130;
  const centerX = 160;
  const centerY = 160;

  return (
    <div style={{ width: "320px", height: "320px", position: "relative", flexShrink: 0 }}>
      <svg width="320" height="320" viewBox="0 0 320 320">
        {/* Anillo de contención */}
        <circle
          cx={centerX}
          cy={centerY}
          r={radius + 15}
          fill="none"
          stroke={`${accent}33`}
          strokeWidth="1"
          strokeDasharray="4 6"
        />

        {/* Líneas de atención cuántica entre nodos */}
        {Array.from({ length: nodeCount }).map((_, i) => {
          const angle1 = (i * (2 * Math.PI)) / nodeCount + (frame * 0.012);
          const x1 = centerX + radius * Math.cos(angle1);
          const y1 = centerY + radius * Math.sin(angle1);

          return Array.from({ length: nodeCount }).map((_, j) => {
            if (j <= i) return null;
            const angle2 = (j * (2 * Math.PI)) / nodeCount + (frame * 0.012);
            const x2 = centerX + radius * Math.cos(angle2);
            const y2 = centerY + radius * Math.sin(angle2);

            const opacity = phaseId === 2 
              ? (Math.sin(frame * 0.2 + i * j) > 0 ? 0.6 : 0.08) // Enlaces parpadeantes en fricción
              : phaseId === 3 
                ? 0.15 // Enlaces rotos en falsación
                : 0.45; // Enlaces armónicos en tesis

            return (
              <line
                key={`${i}-${j}`}
                x1={x1}
                y1={y1}
                x2={x2}
                y2={y2}
                stroke={accent}
                strokeWidth={phaseId === 1 ? "1.5" : "1"}
                strokeOpacity={opacity}
              />
            );
          });
        })}

        {/* Nodos de tokens / valores propios */}
        {Array.from({ length: nodeCount }).map((_, i) => {
          const angle = (i * (2 * Math.PI)) / nodeCount + (frame * 0.012);
          const jitter = phaseId === 2 ? Math.sin(frame * 0.4 + i) * 6 : 0;
          const x = centerX + (radius + jitter) * Math.cos(angle);
          const y = centerY + (radius + jitter) * Math.sin(angle);

          return (
            <g key={i}>
              <circle cx={x} cy={y} r="6" fill={accent} filter="drop-shadow(0 0 6px rgba(0,240,220,0.8))" />
              <circle cx={x} cy={y} r="12" fill="none" stroke={accent} strokeWidth="1" strokeOpacity="0.4" />
            </g>
          );
        })}

        {/* Vector de Falsación Central (Láser destructivo en Fase 3) */}
        {phaseId === 3 && (
          <line
            x1="20"
            y1="300"
            x2="300"
            y2="20"
            stroke="#FF4444"
            strokeWidth="3"
            strokeDasharray="8 4"
            filter="drop-shadow(0 0 10px #FF4444)"
          />
        )}
      </svg>
    </div>
  );
};

// ==============================================================================
// ESCENA INDIVIDUAL CON TIPOGRAFÍA CINÉTICA & FÍSICA LAMP
// ==============================================================================
export const Scene: React.FC<{ data: SceneData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const phaseMeta = PHASE_COLORS[data.phaseId] || PHASE_COLORS[1];

  // LAMP Spring Physics
  const cardScale = spring({ fps, frame, config: data.physics });
  const cardOpacity = spring({ fps, frame, config: { damping: 20 } });

  const badgeY = interpolate(spring({ fps, frame: frame - 6, config: { damping: 15, stiffness: 120 } }), [0, 1], [-25, 0]);
  const badgeOpacity = interpolate(spring({ fps, frame: frame - 6, config: { damping: 15 } }), [0, 1], [0, 1]);

  const words = data.text.split(" ");
  // Fracción temporal de lectura para kinetic subtitle highlight
  const totalWords = words.length;
  const activeWordIdx = Math.floor(interpolate(frame, [15, data.durationInFrames - 15], [0, totalWords], { extrapolateLeft: "clamp", extrapolateRight: "clamp" }));

  const progressWidth = interpolate(frame, [0, data.durationInFrames], [0, 100], { extrapolateRight: "clamp" });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "60px" }}>
      {/* Resplandor reactivo de fondo */}
      <div
        style={{
          position: "absolute",
          width: "1100px",
          height: "550px",
          background: `radial-gradient(circle, ${phaseMeta.glow} 0%, rgba(0,0,0,0) 70%)`,
          filter: "blur(110px)",
          pointerEvents: "none",
        }}
      />

      {/* Tarjeta Glassmórfica Principal */}
      <div
        style={{
          transform: `scale(${cardScale})`,
          opacity: cardOpacity,
          width: "1540px",
          backgroundColor: "rgba(6, 9, 13, 0.88)",
          border: `1px solid ${phaseMeta.border}`,
          borderRadius: "24px",
          padding: "50px 65px",
          boxShadow: `0 32px 100px -16px ${phaseMeta.glow}, 0 0 1px 1px rgba(255,255,255,0.12)`,
          backdropFilter: "blur(28px)",
          display: "flex",
          flexDirection: "column",
          gap: "24px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Cabecera Técnica */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <span style={{ color: phaseMeta.accent, fontSize: "16px", filter: `drop-shadow(0 0 8px ${phaseMeta.accent})` }}>●</span>
            <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "17px", color: "#8B949E", letterSpacing: "2.5px" }}>
              C5-REAL // PROTOCOLO DE FALSACIÓN POPPERIANA (SOTA 2026)
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "15px", color: "#58A6FF", border: "1px solid #1F6FEB", padding: "4px 10px", borderRadius: "4px" }}>
              LEGIÓN-1000 SWARM
            </span>
            <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "17px", color: phaseMeta.accent, fontWeight: "bold" }}>
              FASE 0{data.phaseId} / 03
            </span>
          </div>
        </div>

        {/* Badge Causal & Fórmula Matemática */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div
            style={{
              transform: `translateY(${badgeY}px)`,
              opacity: badgeOpacity,
              display: "inline-flex",
              padding: "8px 22px",
              backgroundColor: "rgba(255, 255, 255, 0.04)",
              border: `1px solid ${phaseMeta.accent}`,
              borderRadius: "8px",
              boxShadow: `0 0 15px ${phaseMeta.glow}`,
            }}
          >
            <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "20px", fontWeight: 800, color: phaseMeta.accent, letterSpacing: "2px" }}>
              {data.phaseTitle.toUpperCase()}
            </span>
          </div>

          <div style={{ fontFamily: "ui-monospace, monospace", fontSize: "16px", color: "#7EE787", backgroundColor: "#041C10", padding: "6px 14px", borderRadius: "6px", border: "1px solid #238636" }}>
            {phaseMeta.formula}
          </div>
        </div>

        {/* Sección Central Dividida: Texto Cinético + Grafo Cuántico Reactivo */}
        <div style={{ display: "flex", gap: "40px", alignItems: "center", margin: "10px 0" }}>
          {/* Bloque de Texto con Tipografía Cinética (Word-by-word highlight) */}
          <div style={{ flex: 1 }}>
            <p
              style={{
                fontFamily: "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
                fontSize: "42px",
                lineHeight: "1.36",
                color: "#F0F6FC",
                letterSpacing: "-0.5px",
                margin: 0,
              }}
            >
              {words.map((word, i) => {
                const isPast = i < activeWordIdx;
                const isCurrent = i === activeWordIdx;
                
                let wordColor = "rgba(240, 246, 252, 0.4)";
                let wordGlow = "none";
                let wordScale = "1";
                
                if (isPast) {
                  wordColor = "#FFFFFF";
                } else if (isCurrent) {
                  wordColor = phaseMeta.accent;
                  wordGlow = `0 0 18px ${phaseMeta.accent}`;
                  wordScale = "1.06";
                }

                return (
                  <span
                    key={i}
                    style={{
                      display: "inline-block",
                      marginRight: "10px",
                      color: wordColor,
                      textShadow: wordGlow,
                      transform: `scale(${wordScale})`,
                      transition: "color 0.1s ease, transform 0.1s ease",
                      fontWeight: isCurrent ? 700 : 400,
                    }}
                  >
                    {word}
                  </span>
                );
              })}
            </p>

            <div style={{ marginTop: "24px", fontFamily: "ui-monospace, monospace", fontSize: "14px", color: "#8B949E", letterSpacing: "1px" }}>
              ▶ {phaseMeta.formulaDesc}
            </div>
          </div>

          {/* Gráfico Cuántico Reactivo de la Atención */}
          <QuantumLatticeGraphic phaseId={data.phaseId} frame={frame} accent={phaseMeta.accent} />
        </div>

        {/* Visualizador de Espectro Acústico */}
        <KineticSpectrumVisualizer phaseId={data.phaseId} frame={frame} accent={phaseMeta.accent} />

        {/* Barra de Progreso Interna */}
        <div
          style={{
            width: "100%",
            height: "5px",
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            borderRadius: "3px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progressWidth}%`,
              height: "100%",
              backgroundColor: phaseMeta.accent,
              boxShadow: `0 0 10px ${phaseMeta.accent}`,
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};

// ==============================================================================
// ROOT DE LA MASTERCLASS
// ==============================================================================
export const BabylonMasterclass: React.FC<{
  title: string;
  sessionHash: string;
  scenes: SceneData[];
}> = ({ title = "INVESTIGACIÓN POPPERIANA", sessionHash = "AX-LEGIÓN-1000", scenes = [] }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ backgroundColor: "#020305", overflow: "hidden" }}>
      {/* Cuadrícula de coordenadas Brutalista SOTA */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px)",
          backgroundSize: "64px 64px",
          opacity: 0.75,
        }}
      />

      {/* Telemetría Global Superior */}
      <AbsoluteFill
        style={{
          top: "35px",
          left: "50px",
          right: "50px",
          height: "40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "ui-monospace, monospace",
          fontSize: "17px",
          color: "#6E7681",
          letterSpacing: "1.5px",
          zIndex: 20,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <span style={{ color: "#FF4444", fontSize: "14px" }}>●</span>
          <span>REC // {sessionHash}</span>
          <span style={{ color: "#E6EDF3", fontWeight: 700 }}>| {title}</span>
        </div>
        <div style={{ display: "flex", gap: "24px" }}>
          <span>FRAME {String(frame).padStart(4, "0")} / 60 FPS</span>
          <span style={{ color: "#00F0DC" }}>EXERGY: 20.950 / 21.000</span>
        </div>
      </AbsoluteFill>

      {/* Render Secuencial de Fases */}
      <AbsoluteFill style={{ zIndex: 10 }}>
        <Series>
          {scenes.map((scene, i) => (
            <Series.Sequence key={i} durationInFrames={scene.durationInFrames}>
              <Scene data={scene} />
            </Series.Sequence>
          ))}
        </Series>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
