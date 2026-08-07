// C5-REAL EXERGY CERTIFIED
import React from "react";
import { AbsoluteFill, Video, Audio, staticFile, useCurrentFrame, interpolate, spring } from "remotion";
import subtitleData from "../public/gon_fiction_subtitles.json";
import { SubtitleItem } from "./types";

const subtitles = subtitleData as SubtitleItem[];
const lastSubtitle = subtitles[subtitles.length - 1];
export const GON_FICTION_DURATION_FRAMES = lastSubtitle ? lastSubtitle.endFrame + 150 : 22200;

export const GonFictionComposition: React.FC = () => {
  const frame = useCurrentFrame();

  const activeSub = subtitles.find(
    (s) => frame >= s.startFrame && frame <= s.endFrame
  ) || null;

  const isSilence = activeSub === null || activeSub.speaker === "PAUSA";

  // Hyper-kinetic trig/spring animations for mouth & avatar physics
  const isSpeaking = !isSilence;
  const mouthScaleY = isSpeaking ? 1.0 + 0.4 * Math.abs(Math.sin(frame * 0.9)) : 0.8;
  const mouthScaleX = isSpeaking ? 1.0 + 0.15 * Math.cos(frame * 0.7) : 1.0;
  const headRotation = isSpeaking ? Math.sin(frame * 0.45) * 8 : 0;
  const pulseAura = isSpeaking ? 25 + 15 * Math.abs(Math.sin(frame * 0.8)) : 10;

  // Character-based screen shake (Chicote & Flea generate intense kinetic jitter)
  const isHypedCharacter = activeSub && (activeSub.speaker === "CHICOTE" || activeSub.speaker === "FLEA" || activeSub.speaker === "FRUSCIANTE");
  const jitterX = isSpeaking && isHypedCharacter ? (Math.sin(frame * 1.5) * 6) : 0;
  const jitterY = isSpeaking && isHypedCharacter ? (Math.cos(frame * 1.8) * 6) : 0;

  // Spring animation for entrance when speaker changes
  const speakerEntrance = spring({
    fps: 30,
    frame: activeSub ? frame - activeSub.startFrame : 0,
    config: { damping: 12, stiffness: 180 },
  });

  // Dynamic Location HUD Mapping based on subtitle index
  const getLocation = (id: number) => {
    if (id <= 6) return "📍 MUELLE DE MARZANA";
    if (id <= 14) return "📍 CALLE SAN FRANCISCO";
    if (id <= 20) return "📍 TABERNA KERNEL // RING-0";
    if (id <= 27) return "📍 PUENTE DE LA SALVE";
    if (id <= 32) return "📍 URGENCIAS BILBI";
    if (id <= 37) return "📍 CASCO VIEJO DE BILBAO";
    return "📍 PUENTE SAN ANTÓN // ESTACIÓN FINAL";
  };

  const currentLocation = activeSub ? getLocation(activeSub.id) : "📍 BILBAO LA VIEJA";
  const score = Math.floor(frame * 12.5);
  const healthBars = "♥♥♥♥♥";

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#020005",
        overflow: "hidden",
        fontFamily: "'Press Start 2P', monospace, sans-serif",
        transform: `translate(${jitterX}px, ${jitterY}px)`,
      }}
    >
      {/* 1. BACKGROUND: FFmpeg Kinetic 8-Bit Render */}
      <Video
        src={staticFile("out_gon_fiction_8bit.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.85 }}
      />

      {/* 2. CRT SCANLINES & VIGNETTE OVERLAY */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          background:
            "linear-gradient(rgba(18, 16, 16, 0) 50%, rgba(0, 0, 0, 0.4) 50%), linear-gradient(90deg, rgba(255, 0, 0, 0.03), rgba(0, 255, 0, 0.01), rgba(0, 0, 255, 0.03))",
          backgroundSize: "100% 4px, 6px 100%",
          pointerEvents: "none",
          zIndex: 5,
        }}
      />

      {/* 3. ARCADE HUD (TOP HEADER) */}
      <div
        style={{
          position: "absolute",
          top: "40px",
          left: "40px",
          right: "40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "#00F0FF",
          fontSize: "20px",
          textShadow: "3px 3px 0px #000, 0 0 10px #00F0FF",
          zIndex: 10,
        }}
      >
        <div>
          <span style={{ color: "#FFD300" }}>P1:</span> GON & CHICOTE
        </div>
        <div style={{ color: "#FF6600", fontSize: "16px" }}>{currentLocation}</div>
        <div>
          <span style={{ color: "#FF0055" }}>LIFE:</span> <span style={{ color: "#FF3333" }}>{healthBars}</span>
        </div>
        <div>
          <span style={{ color: "#00FF66" }}>SCORE:</span> {score.toString().padStart(6, "0")}
        </div>
      </div>

      {/* 4. SUBTITLE / DIALOGUE & AVATAR LAYER */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "flex-end",
          padding: "80px 40px 140px 40px",
          boxSizing: "border-box",
          zIndex: 10,
        }}
      >
        {activeSub && !isSilence && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "24px",
              width: "100%",
              transform: `scale(${speakerEntrance})`,
              opacity: interpolate(speakerEntrance, [0, 1], [0, 1]),
            }}
          >
            {/* AVATAR WITH DYNAMIC LIP SYNC PHYSICS */}
            <div
              style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transform: `rotate(${headRotation}deg)`,
              }}
            >
              {/* Pulsing Aura */}
              <div
                style={{
                  position: "absolute",
                  width: "170px",
                  height: "170px",
                  borderRadius: "50%",
                  backgroundColor: activeSub.color,
                  opacity: 0.4,
                  filter: `blur(${pulseAura}px)`,
                }}
              />

              {/* Avatar Emoji Container */}
              <div
                style={{
                  fontSize: "130px",
                  transform: `scale(${mouthScaleX}, ${mouthScaleY})`,
                  filter: `drop-shadow(0px 10px 25px ${activeSub.color})`,
                  zIndex: 2,
                }}
              >
                {activeSub.avatar}
              </div>
            </div>

            {/* SPEAKER NAME BADGE */}
            <div
              style={{
                fontSize: "30px",
                fontWeight: 900,
                color: activeSub.color,
                backgroundColor: "#000000D0",
                padding: "12px 28px",
                borderRadius: "8px",
                border: `3px solid ${activeSub.color}`,
                boxShadow: `0 0 20px ${activeSub.color}80, inset 0 0 10px ${activeSub.color}40`,
                letterSpacing: "4px",
                textTransform: "uppercase",
              }}
            >
              👾 {activeSub.speaker}
            </div>

            {/* TEXT DIALOGUE BOX (ARCADE DIALOGUE STYLE) */}
            <div
              style={{
                width: "100%",
                backgroundColor: "rgba(5, 5, 15, 0.94)",
                border: `4px solid ${activeSub.color}`,
                borderRadius: "16px",
                padding: "36px 40px",
                boxShadow: `0 0 35px ${activeSub.color}60, inset 0 0 15px rgba(255,255,255,0.05)`,
                boxSizing: "border-box",
                display: "flex",
                flexDirection: "column",
                gap: "16px",
              }}
            >
              <div
                style={{
                  fontSize: "44px",
                  lineHeight: "1.4",
                  color: "#FFFFFF",
                  fontFamily: "Inter, system-ui, sans-serif",
                  fontWeight: 800,
                  textAlign: "center",
                  textShadow: "0 4px 10px rgba(0,0,0,0.9)",
                }}
              >
                "{activeSub.text}"
              </div>
            </div>
          </div>
        )}

        {/* PAUSE / SILENCE DISPLAY */}
        {isSilence && (
          <div
            style={{
              backgroundColor: "rgba(0,0,0,0.85)",
              border: "3px dashed #FFD300",
              padding: "24px 40px",
              borderRadius: "12px",
              color: "#FFD300",
              fontSize: "24px",
              letterSpacing: "3px",
              textShadow: "0 0 10px #FFD300",
              marginBottom: "100px",
            }}
          >
            ⏳ PAUSA ONTOLÓGICA EN BILBAO LA VIEJA...
          </div>
        )}
      </div>

      {/* 5. REACT EQUALIZER BARS (BOTTOM ACCENT) */}
      <div
        style={{
          position: "absolute",
          bottom: "60px",
          left: "40px",
          right: "40px",
          height: "30px",
          display: "flex",
          gap: "8px",
          alignItems: "flex-end",
          justifyContent: "center",
          zIndex: 10,
        }}
      >
        {Array.from({ length: 32 }).map((_, i) => {
          const barHeight = isSpeaking
            ? Math.max(10, Math.sin(frame * 0.3 + i * 0.4) * 28 + 15)
            : 4;
          const barColor = activeSub ? activeSub.color : "#00F0FF";
          return (
            <div
              key={i}
              style={{
                width: "18px",
                height: `${barHeight}px`,
                backgroundColor: barColor,
                boxShadow: `0 0 8px ${barColor}`,
                borderRadius: "3px",
                transition: "height 60ms ease-out",
              }}
            />
          );
        })}
      </div>

      {/* 6. FOOTER / SYSTEM STATUS */}
      <div
        style={{
          position: "absolute",
          bottom: "20px",
          left: "40px",
          right: "40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          color: "rgba(255, 255, 255, 0.4)",
          fontSize: "12px",
          zIndex: 10,
        }}
      >
        <div>C5-REAL KERNEL: ACTIVE</div>
        <div>BILBO ZAHARRA // 8-BIT NES EDITION</div>
      </div>

      {/* 7. MASTER AUDIO TRACK */}
      <Audio src={staticFile("gon_fiction_master.wav")} volume={1.0} />
    </AbsoluteFill>
  );
};
