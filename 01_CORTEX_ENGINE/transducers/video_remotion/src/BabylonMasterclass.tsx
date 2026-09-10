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

const PHASE_COLORS: Record<number, { accent: string; glow: string; border: string }> = {
  1: { accent: "#00F0DC", glow: "rgba(0, 240, 220, 0.35)", border: "rgba(0, 240, 220, 0.4)" }, // Cyan (Tesis)
  2: { accent: "#FFB428", glow: "rgba(255, 180, 40, 0.35)", border: "rgba(255, 180, 40, 0.4)" }, // Amber (Fricción)
  3: { accent: "#FF4444", glow: "rgba(255, 68, 68, 0.45)", border: "rgba(255, 68, 68, 0.5)" },   // Crimson (Falsación)
};

export const Scene: React.FC<{ data: SceneData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const colors = PHASE_COLORS[data.phaseId] || PHASE_COLORS[1];

  // Staggered Spring Physics (LAMP Protocol)
  const cardScale = spring({
    fps,
    frame,
    config: data.physics,
  });

  const cardOpacity = spring({
    fps,
    frame,
    config: { damping: 20 },
  });

  const badgeY = interpolate(
    spring({ fps, frame: frame - 6, config: { damping: 15, stiffness: 120 } }),
    [0, 1],
    [-20, 0]
  );

  const badgeOpacity = interpolate(
    spring({ fps, frame: frame - 6, config: { damping: 15 } }),
    [0, 1],
    [0, 1]
  );

  const textY = interpolate(
    spring({ fps, frame: frame - 12, config: data.physics }),
    [0, 1],
    [30, 0]
  );

  const textOpacity = interpolate(
    spring({ fps, frame: frame - 12, config: { damping: 18 } }),
    [0, 1],
    [0, 1]
  );

  const progressWidth = interpolate(frame, [0, data.durationInFrames], [0, 100], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: "60px" }}>
      {/* Background Reactive Ambient Glow */}
      <div
        style={{
          position: "absolute",
          width: "900px",
          height: "450px",
          background: `radial-gradient(circle, ${colors.glow} 0%, rgba(0,0,0,0) 70%)`,
          filter: "blur(90px)",
          pointerEvents: "none",
        }}
      />

      {/* Main Glassmorphic Card Container */}
      <div
        style={{
          transform: `scale(${cardScale})`,
          opacity: cardOpacity,
          width: "1480px",
          backgroundColor: "rgba(8, 11, 16, 0.82)",
          border: `1px solid ${colors.border}`,
          borderRadius: "20px",
          padding: "60px 70px",
          boxShadow: `0 24px 80px -12px ${colors.glow}, 0 0 1px 1px rgba(255,255,255,0.08)`,
          backdropFilter: "blur(24px)",
          display: "flex",
          flexDirection: "column",
          gap: "28px",
          position: "relative",
          overflow: "hidden",
        }}
      >
        {/* Card Top Metadata */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ color: colors.accent, fontSize: "14px" }}>●</span>
            <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "16px", color: "#8B949E", letterSpacing: "2px" }}>
              C5-REAL // PROTOCOLO DE FALSACIÓN POPPERIANA
            </span>
          </div>
          <span style={{ fontFamily: "ui-monospace, monospace", fontSize: "16px", color: colors.accent, fontWeight: "bold" }}>
            FASE 0{data.phaseId} / 03
          </span>
        </div>

        {/* Phase Badge */}
        <div
          style={{
            transform: `translateY(${badgeY}px)`,
            opacity: badgeOpacity,
            display: "inline-flex",
            alignSelf: "flex-start",
            padding: "8px 20px",
            backgroundColor: "rgba(255, 255, 255, 0.04)",
            border: `1px solid ${colors.accent}`,
            borderRadius: "8px",
          }}
        >
          <span
            style={{
              fontFamily: "ui-monospace, monospace",
              fontSize: "20px",
              fontWeight: 700,
              color: colors.accent,
              letterSpacing: "1.5px",
            }}
          >
            {data.phaseTitle.toUpperCase()}
          </span>
        </div>

        {/* Core Epistemic Voiceover Statement */}
        <div style={{ transform: `translateY(${textY}px)`, opacity: textOpacity, margin: "10px 0 20px 0" }}>
          <p
            style={{
              fontFamily: "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', sans-serif",
              fontSize: "44px",
              lineHeight: "1.32",
              color: "#F0F6FC",
              fontWeight: 400,
              letterSpacing: "-0.5px",
              margin: 0,
            }}
          >
            {data.text}
          </p>
        </div>

        {/* Progress Bar within Card */}
        <div
          style={{
            width: "100%",
            height: "4px",
            backgroundColor: "rgba(255, 255, 255, 0.08)",
            borderRadius: "2px",
            overflow: "hidden",
          }}
        >
          <div
            style={{
              width: `${progressWidth}%`,
              height: "100%",
              backgroundColor: colors.accent,
              borderRadius: "2px",
            }}
          />
        </div>
      </div>
    </AbsoluteFill>
  );
};

export const BabylonMasterclass: React.FC<{
  title: string;
  sessionHash: string;
  scenes: SceneData[];
}> = ({ title = "INVESTIGACIÓN POPPERIANA", sessionHash = "AX-SOTA", scenes = [] }) => {
  return (
    <AbsoluteFill style={{ backgroundColor: "#030303", overflow: "hidden" }}>
      {/* Brutalist Grid Background */}
      <AbsoluteFill
        style={{
          backgroundImage:
            "linear-gradient(rgba(255,255,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.04) 1px, transparent 1px)",
          backgroundSize: "70px 70px",
          opacity: 0.7,
        }}
      />

      {/* Screen Corner Telemetry */}
      <AbsoluteFill
        style={{
          top: "40px",
          left: "50px",
          right: "50px",
          height: "40px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontFamily: "ui-monospace, monospace",
          fontSize: "18px",
          color: "#6E7681",
          letterSpacing: "1px",
        }}
      >
        <div>
          <span style={{ color: "#E6EDF3", fontWeight: "bold" }}>{sessionHash}</span> | {title}
        </div>
        <div>60 FPS // 1080P PRORES-READY</div>
      </AbsoluteFill>

      {/* Render Sequences */}
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
