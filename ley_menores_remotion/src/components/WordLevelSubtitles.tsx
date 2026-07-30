// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export interface WordTimestamp {
  word: string;
  startFrame: number;
  endFrame: number;
}

export interface WordLevelSubtitlesProps {
  timestamps: WordTimestamp[];
  activeColor?: string;
}

export const WordLevelSubtitles: React.FC<WordLevelSubtitlesProps> = ({
  timestamps,
  activeColor = "#8b5cf6"
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  if (!timestamps || timestamps.length === 0) return null;

  return (
    <div
      style={{
        position: "absolute",
        bottom: 80,
        left: 60,
        right: 60,
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: "12px",
        padding: "24px 36px",
        backgroundColor: "rgba(15, 23, 42, 0.75)",
        backdropFilter: "blur(20px)",
        borderRadius: "20px",
        border: "1px solid rgba(255, 255, 255, 0.15)",
        boxShadow: "0 20px 50px rgba(0, 0, 0, 0.5)"
      }}
    >
      {timestamps.map((wt, idx) => {
        const isActive = frame >= wt.startFrame && frame <= wt.endFrame;
        const isPast = frame > wt.endFrame;

        const scale = isActive
          ? spring({ frame: frame - wt.startFrame, fps, config: { damping: 12, stiffness: 200 } })
          : 1;

        return (
          <span
            key={idx}
            style={{
              fontSize: "36px",
              fontWeight: 800,
              fontFamily: "Inter, system-ui, sans-serif",
              color: isActive ? activeColor : isPast ? "#94a3b8" : "#ffffff",
              transform: `scale(${isActive ? Math.max(1, scale * 1.15) : 1})`,
              transition: "color 0.15s ease",
              textShadow: isActive ? `0 0 20px ${activeColor}` : "0 2px 4px rgba(0,0,0,0.5)",
              display: "inline-block"
            }}
          >
            {wt.word}
          </span>
        );
      })}
    </div>
  );
};
