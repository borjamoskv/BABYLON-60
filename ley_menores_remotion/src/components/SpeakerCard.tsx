// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export interface SpeakerCardProps {
  speaker: string;
  voice: string;
  color?: string;
}

export const SpeakerCard: React.FC<SpeakerCardProps> = ({
  speaker,
  voice,
  color = "#8b5cf6"
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    frame,
    fps,
    config: { damping: 14, stiffness: 150 }
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 60,
        left: 60,
        display: "flex",
        alignItems: "center",
        gap: "18px",
        padding: "16px 28px",
        backgroundColor: "rgba(15, 23, 42, 0.85)",
        backdropFilter: "blur(20px)",
        borderRadius: "16px",
        border: `2px solid ${color}`,
        transform: `translateY(${Math.max(0, (1 - entrance) * -50)}px)`,
        opacity: Math.min(1, entrance),
        boxShadow: `0 10px 30px ${color}44`
      }}
    >
      <div
        style={{
          width: "48px",
          height: "48px",
          borderRadius: "50%",
          backgroundColor: color,
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          color: "#ffffff",
          fontWeight: 900,
          fontSize: "22px",
          boxShadow: `0 0 15px ${color}`
        }}
      >
        {speaker.charAt(0)}
      </div>

      <div style={{ display: "flex", flexDirection: "column" }}>
        <span
          style={{
            fontSize: "24px",
            fontWeight: 800,
            color: "#ffffff",
            fontFamily: "Inter, sans-serif"
          }}
        >
          {speaker}
        </span>
        <span
          style={{
            fontSize: "14px",
            fontWeight: 600,
            color: color,
            fontFamily: "monospace",
            textTransform: "uppercase",
            letterSpacing: "1px"
          }}
        >
          VOZ: {voice} (TTS)
        </span>
      </div>
    </div>
  );
};
