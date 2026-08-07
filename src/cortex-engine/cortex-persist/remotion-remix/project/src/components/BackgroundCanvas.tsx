// C5-REAL EXERGY CERTIFIED
import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

export const BackgroundCanvas: React.FC<{ activeColor?: string }> = ({ activeColor = "#00F0FF" }) => {
  const frame = useCurrentFrame();

  const glowOpacity = interpolate(
    Math.sin(frame / 15),
    [-1, 1],
    [0.2, 0.55]
  );

  const rotateDeg = (frame * 0.4) % 360;
  const pulseScale = interpolate(Math.sin(frame * 0.08), [-1, 1], [0.95, 1.08]);

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#080911",
        overflow: "hidden",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      {/* Dynamic Cyber Grid */}
      <div
        style={{
          position: "absolute",
          inset: "-50%",
          backgroundImage: `
            linear-gradient(to right, rgba(255, 255, 255, 0.06) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.06) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          transform: `rotate(${rotateDeg * 0.05}deg)`,
          opacity: 0.35,
        }}
      />

      {/* Sagittarius A* Black Hole Event Horizon Ring */}
      <div
        style={{
          position: "absolute",
          width: "600px",
          height: "600px",
          borderRadius: "50%",
          border: `3px stroke ${activeColor}`,
          boxShadow: `0 0 80px ${activeColor}, inset 0 0 60px ${activeColor}`,
          transform: `scale(${pulseScale}) rotate(${rotateDeg}deg)`,
          opacity: 0.45,
          filter: "blur(4px)",
        }}
      />

      {/* Reactive Deep Space Radial Glow */}
      <div
        style={{
          position: "absolute",
          width: "900px",
          height: "900px",
          borderRadius: "50%",
          background: `radial-gradient(circle, ${activeColor} 0%, transparent 70%)`,
          opacity: glowOpacity,
          filter: "blur(100px)",
        }}
      />
    </AbsoluteFill>
  );
};
