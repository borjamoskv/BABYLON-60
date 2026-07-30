// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export interface ChapterTitleSceneProps {
  chapterTitle: string;
  subtitle?: string;
}

export const ChapterTitleScene: React.FC<ChapterTitleSceneProps> = ({
  chapterTitle,
  subtitle
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const scale = spring({
    frame,
    fps,
    config: { damping: 15, stiffness: 120 }
  });

  const opacity = Math.min(1, frame / 15);

  return (
    <div
      style={{
        position: "absolute",
        top: 60,
        right: 60,
        display: "flex",
        flexDirection: "column",
        alignItems: "flex-end",
        gap: "6px",
        padding: "16px 24px",
        backgroundColor: "rgba(2, 6, 23, 0.8)",
        backdropFilter: "blur(16px)",
        borderRadius: "14px",
        borderRight: "4px solid #38bdf8",
        borderTop: "1px solid rgba(255, 255, 255, 0.1)",
        transform: `scale(${scale})`,
        opacity
      }}
    >
      <span
        style={{
          fontSize: "12px",
          fontWeight: 900,
          color: "#38bdf8",
          fontFamily: "monospace",
          letterSpacing: "2px",
          textTransform: "uppercase"
        }}
      >
        DOCUMENTAL DE INVESTIGACIÓN SOTA
      </span>
      <span
        style={{
          fontSize: "20px",
          fontWeight: 800,
          color: "#f8fafc",
          fontFamily: "Inter, sans-serif"
        }}
      >
        {chapterTitle}
      </span>
      {subtitle && (
        <span
          style={{
            fontSize: "14px",
            fontWeight: 500,
            color: "#94a3b8",
            fontFamily: "Inter, sans-serif"
          }}
        >
          {subtitle}
        </span>
      )}
    </div>
  );
};
