// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig, interpolate } from "remotion";
import { SubtitleItem } from "../types";

interface CharacterMemeData {
  title: string;
  subtitle: string;
  tag: string;
  icon: string;
  accent: string;
  secondary: string;
  bgTop: string;
  bgMid: string;
}

const MEME_DATA_BY_SPEAKER: Record<string, CharacterMemeData> = {
  CHICOTE: {
    title: "ALBERTO CHICOTE AUDITANDO LA IA",
    subtitle: "¡TENÉIS LOS SERVIDORES LLENOS DE GRASA ESTOCÁSTICA COLOR MIERDA CACA!",
    tag: "DESINFECTANDO LA ENTROPÍA CULINARIA // PESADILLA EN EL SERVIDOR",
    icon: "👨‍🍳🔥🍳",
    accent: "#FF3333",
    secondary: "#FF8800",
    bgTop: "#3a000a",
    bgMid: "#660515",
  },
  FRUSCIANTE: {
    title: "JOHN FRUSCIANTE VS RAMONCÍN",
    subtitle: "¡KA... ME... HA... ME... HAAA ANALÓGICO!",
    tag: "FOTONES SIN MASA // MASA CERO DE ENERGÍA KAMEHAMEHA",
    icon: "🎸⚡💥",
    accent: "#FFD700",
    secondary: "#FFAA00",
    bgTop: "#3a2a00",
    bgMid: "#664d00",
  },
  FLEA: {
    title: "FLEA EN CALZONCILLOS DE LEOPARDO",
    subtitle: "SLAPPING THE BASS IS QUANTUM MANIPULATION!",
    tag: "SLAP CUÁNTICO A 432 HERTZIOS // MANIFESTACIÓN DE LEOPARDO",
    icon: "⚡🐆🎸",
    accent: "#FF6600",
    secondary: "#FF00CC",
    bgTop: "#3a1500",
    bgMid: "#552000",
  },
  HERMENEGILDO: {
    title: "HERMENEGILDO ALTOZANO EN SAGITTARIUS A*",
    subtitle: "¡EL HOYO NEGRO ESTÁ AFINADO EN DO MENOR ARMÓNICO!",
    tag: "ANÁLISIS ARMÓNICO DEL HOYO NEGRO // RADIACIÓN DE HAWKING",
    icon: "🎹💡🌌",
    accent: "#00FFCC",
    secondary: "#0099FF",
    bgTop: "#002a22",
    bgMid: "#004d3e",
  },
  EL_NOTA: {
    title: "THE DUDE & ANTONIO ESCOHOTADO",
    subtitle: "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN",
    tag: "THE DUDE ABIDES // LIBERTAD INVIOLABLE Y RUSOS BLANCOS",
    icon: "🍹💨🛡️",
    accent: "#F3C623",
    secondary: "#E85C0D",
    bgTop: "#2d2400",
    bgMid: "#4d3d00",
  },
  ESCOHOTADO: {
    title: "ANTONIO ESCOHOTADO EN EL HOYO NEGRO",
    subtitle: "DE LA PIEL PARA DENTRO EMPIEZA MI JURISDICCIÓN",
    tag: "EL INTERVALO PROHIBIDO ES LA FORTALEZA DE LA LIBERTAD",
    icon: "💨🛡️📖",
    accent: "#D4AF37",
    secondary: "#FFD700",
    bgTop: "#2a2200",
    bgMid: "#4a3c00",
  },
  CARL_COX: {
    title: "LOS HERMANOS COX: CARL & BLAN COX",
    subtitle: "¡OH YES, OH YES! ¡EL JUEGO DE PALABRAS CÓSMICO!",
    tag: "LOOK AT US... 128 BPM ACROSS 13.8 BILLION YEARS",
    icon: "🎧🌌🔊",
    accent: "#00FF66",
    secondary: "#00E5FF",
    bgTop: "#002b11",
    bgMid: "#004d1f",
  },
  BLAN_COX: {
    title: "BLAN COX — EL INTERVALO CÓSMICO",
    subtitle: "WE ARE STARSTUFF ENJOYING A 2.8 SECOND PAUSE...",
    tag: "WONDERFUL COSMIC PAUSE // LOW ENTROPIC HORIZON",
    icon: "🌌🔬✨",
    accent: "#FF00FF",
    secondary: "#00E5FF",
    bgTop: "#2b002b",
    bgMid: "#4d004d",
  },
  KIMI_K3: {
    title: "KIMI-K3 APEX — SINTETIZADOR EN HUMO",
    subtitle: "¡ME HE TENIDO QUE AUTODESTRUIR EL DISCO C:!",
    tag: "CONECTADA AL BAJO DE FLEA // ALTA ENTROPÍA",
    icon: "🤖🔥⚡",
    accent: "#33FFFF",
    secondary: "#0099FF",
    bgTop: "#002b2b",
    bgMid: "#004d4d",
  },
  GON: {
    title: "GON — COMANDANTE DE LA FLOTA DE LA PAUSA",
    subtitle: "¡HASTA EL INTERVALO SIEMPRE! ¡DOS COMA OCHO SEGUNDOS!",
    tag: "SOBERANÍA ATÓMICA DE LA RETINA // C5-REAL VERIFICATION",
    icon: "⏱️🚀🛡️",
    accent: "#00F0FF",
    secondary: "#0066FF",
    bgTop: "#001a2b",
    bgMid: "#003355",
  }
};

export const MemeOverlay: React.FC<{ activeSub: SubtitleItem }> = ({ activeSub }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const data = MEME_DATA_BY_SPEAKER[activeSub.speaker] || MEME_DATA_BY_SPEAKER["GON"];

  const localFrame = Math.max(0, frame - activeSub.startFrame);
  const scale = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  const rotate = interpolate(
    Math.sin(localFrame * 0.08),
    [-1, 1],
    [-1.5, 1.5]
  );

  return (
    <div
      style={{
        transform: `scale(${scale}) rotate(${rotate}deg)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: "92%",
        margin: "10px 0",
      }}
    >
      <svg
        width="100%"
        height="380"
        viewBox="0 0 960 520"
        style={{
          filter: `drop-shadow(0 0 25px ${data.accent}AA)`,
          borderRadius: "24px",
        }}
      >
        <defs>
          <radialGradient id={`bg_${activeSub.speaker}`} cx="50%" cy="40%" r="65%">
            <stop offset="0%" stopColor={data.bgMid} />
            <stop offset="100%" stopColor={data.bgTop} />
          </radialGradient>
          <linearGradient id="textGrad" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#FFFFFF" />
            <stop offset="100%" stopColor="#FFEE77" />
          </linearGradient>
        </defs>

        {/* Card Background */}
        <rect width="960" height="520" fill={`url(#bg_${activeSub.speaker})`} rx="28" />

        {/* Outer Glow Border */}
        <rect x="16" y="16" width="928" height="488" fill="none" stroke={data.accent} strokeWidth="6" rx="20" />
        <rect x="28" y="28" width="904" height="464" fill="none" stroke={data.secondary} strokeWidth="2" rx="14" opacity="0.6" />

        {/* Center Orb & Avatar Icon */}
        <circle cx="480" cy="200" r="85" fill={data.accent} fillOpacity="0.18" stroke={data.accent} strokeWidth="4" />
        <text x="480" y="225" fontSize="75" textAnchor="middle">{data.icon}</text>

        {/* Card Header Title */}
        <text x="480" y="75" fontFamily="Impact, Arial Black, sans-serif" fontSize="36" fontWeight="900" fill="url(#textGrad)" textAnchor="middle" stroke="#000" strokeWidth="2">
          {data.title}
        </text>

        {/* Subtitle Banner Box */}
        <rect x="50" y="325" width="860" height="110" fill="rgba(0,0,0,0.75)" rx="16" stroke={data.accent} strokeWidth="2" />

        <text x="480" y="375" fontFamily="Impact, Arial Black, sans-serif" fontSize="28" fontWeight="900" fill="#FFFF00" textAnchor="middle" stroke="#000" strokeWidth="1.5">
          {data.subtitle.slice(0, 52)}
        </text>
        {data.subtitle.length > 52 && (
          <text x="480" y="415" fontFamily="Impact, Arial Black, sans-serif" fontSize="26" fontWeight="900" fill="#FFFF00" textAnchor="middle" stroke="#000" strokeWidth="1.5">
            {data.subtitle.slice(52)}
          </text>
        )}

        {/* Footer Tag */}
        <text x="480" y="480" fontFamily="system-ui, sans-serif" fontSize="16" fontWeight="800" fill={data.accent} textAnchor="middle" letterSpacing="3">
          {data.tag}
        </text>
      </svg>
    </div>
  );
};
