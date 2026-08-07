// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig } from "remotion";

export const AudioSpectrum: React.FC<{ activeColor: string; isSilence?: boolean }> = ({
  activeColor,
  isSilence = false,
}) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const numBars = 32;

  return (
    <div
      style={{
        display: "flex",
        alignItems: "flex-end",
        justifyContent: "center",
        gap: "6px",
        height: "120px",
        width: "100%",
        padding: "0 20px",
        boxSizing: "border-box",
      }}
    >
      {Array.from({ length: numBars }).map((_, i) => {
        // Frequency simulation based on frame and bar index
        const freq = (i + 1) * 0.4;
        const waveVal = Math.sin(frame * 0.25 + freq);
        const waveVal2 = Math.cos(frame * 0.15 + i * 0.2);

        let heightPercent = isSilence
          ? 4
          : Math.max(8, Math.min(100, ((waveVal + waveVal2 + 2) / 4) * 90 + Math.random() * 10));

        return (
          <div
            key={i}
            style={{
              flex: 1,
              height: `${heightPercent}%`,
              backgroundColor: activeColor,
              borderRadius: "4px 4px 0 0",
              boxShadow: `0 0 12px ${activeColor}`,
              transition: "height 0.05s ease-in-out",
              opacity: isSilence ? 0.3 : 0.85,
            }}
          />
        );
      })}
    </div>
  );
};
