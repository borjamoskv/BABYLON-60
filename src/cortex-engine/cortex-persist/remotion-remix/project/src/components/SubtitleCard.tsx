// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";
import { SubtitleItem } from "../types";

export const SubtitleCard: React.FC<{ item: SubtitleItem }> = ({ item }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Entrance spring animation
  const localFrame = Math.max(0, frame - item.startFrame);
  const scale = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 120 },
  });

  const isSilence = item.speaker === "PAUSA";

  return (
    <div
      style={{
        transform: `scale(${scale})`,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px 36px",
        borderRadius: "20px",
        backgroundColor: "rgba(15, 18, 35, 0.88)",
        border: `3px solid ${item.color}`,
        boxShadow: `0 0 40px ${item.color}66, inset 0 0 20px ${item.color}33`,
        backdropFilter: "blur(12px)",
        maxWidth: "85%",
        textAlign: "center",
        boxSizing: "border-box",
      }}
    >
      {/* Header Badge */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "12px",
          marginBottom: "16px",
          padding: "6px 18px",
          borderRadius: "30px",
          backgroundColor: `${item.color}22`,
          border: `1px solid ${item.color}`,
        }}
      >
        <span style={{ fontSize: "28px" }}>{item.avatar}</span>
        <span
          style={{
            fontSize: "22px",
            fontWeight: 800,
            color: item.color,
            letterSpacing: "2px",
            fontFamily: "system-ui, sans-serif",
            textTransform: "uppercase",
          }}
        >
          {item.speaker.replace("_", " ")}
        </span>
      </div>

      {/* Main Subtitle Text */}
      <div
        style={{
          fontSize: isSilence ? "28px" : "32px",
          fontWeight: 700,
          color: "#FFFFFF",
          lineHeight: 1.4,
          fontFamily: "Inter, system-ui, sans-serif",
          textShadow: `0 2px 10px rgba(0,0,0,0.8), 0 0 20px ${item.color}AA`,
        }}
      >
        {item.text}
      </div>
    </div>
  );
};
