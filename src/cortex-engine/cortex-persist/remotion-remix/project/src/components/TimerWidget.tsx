// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, interpolate } from "remotion";
import { SubtitleItem } from "../types";

export const TimerWidget: React.FC<{ item: SubtitleItem }> = ({ item }) => {
  const frame = useCurrentFrame();

  const pauseDurationFrames = item.endFrame - item.startFrame;
  const elapsedInPause = Math.max(0, Math.min(pauseDurationFrames, frame - item.startFrame));
  const progressRatio = elapsedInPause / Math.max(1, pauseDurationFrames);

  // Time counting up from 0.00s to 2.80s
  const currentSeconds = (progressRatio * 2.8).toFixed(2);

  const ringRotate = interpolate(frame, [item.startFrame, item.endFrame], [0, 360]);

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        gap: "16px",
      }}
    >
      <div
        style={{
          position: "relative",
          width: "220px",
          height: "220px",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "rgba(10, 12, 28, 0.9)",
          border: "4px solid #00F0FF",
          boxShadow: "0 0 50px #00F0FFaa, inset 0 0 30px #00F0FF55",
        }}
      >
        {/* Animated Outer Ring */}
        <div
          style={{
            position: "absolute",
            inset: "-12px",
            borderRadius: "50%",
            border: "3px dashed #00F0FF",
            transform: `rotate(${ringRotate}deg)`,
            opacity: 0.8,
          }}
        />

        {/* Digital Seconds Display */}
        <div
          style={{
            fontSize: "48px",
            fontWeight: 900,
            color: "#00F0FF",
            fontFamily: "monospace",
            textShadow: "0 0 20px #00F0FF",
          }}
        >
          {currentSeconds}s
        </div>
      </div>

      <div
        style={{
          fontSize: "20px",
          fontWeight: 700,
          color: "#FFFFFF",
          letterSpacing: "4px",
          fontFamily: "system-ui, sans-serif",
        }}
      >
        VENTANA DE INTEGRACIÓN TEMPORAL
      </div>
    </div>
  );
};
