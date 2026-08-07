// C5-REAL EXERGY CERTIFIED
import React from "react";
import { AbsoluteFill, useCurrentFrame, interpolate } from "remotion";

export const BackgroundCanvas: React.FC<{ activeColor?: string }> = ({ activeColor = "#00F0FF" }) => {
  const frame = useCurrentFrame();

  // Subtle pulsing grid & radial glow
  const glowOpacity = interpolate(
    Math.sin(frame / 15),
    [-1, 1],
    [0.15, 0.45]
  );

  const rotateDeg = (frame * 0.2) % 360;

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
            linear-gradient(to right, rgba(255, 255, 255, 0.05) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(255, 255, 255, 0.05) 1px, transparent 1px)
          `,
          backgroundSize: "60px 60px",
          transform: `rotate(${rotateDeg * 0.1}deg)`,
          opacity: 0.3,
        }}
      />

      {/* Reactive Radial Glow based on Speaker Color */}
      <div
        style={{
          position: "absolute",
          width: "800px",
          height: "800px",
          borderRadius: "50%",
          background: `radial-gradient(circle, ${activeColor} 0%, transparent 70%)`,
          opacity: glowOpacity,
          filter: "blur(90px)",
          transition: "background 0.5s ease",
        }}
      />
    </AbsoluteFill>
  );
};
