// C5-REAL EXERGY CERTIFIED
import { AbsoluteFill, Composition, staticFile, Loop, OffthreadVideo, Audio, useCurrentFrame } from "remotion";
import React from "react";

export const MyComposition = () => {
  // 2:31 = 151 seconds. 151 * 30 = 4530 frames.
  return (
    <Composition
      id="MyComp"
      component={MyComponent}
      durationInFrames={4530}
      fps={30}
      width={720}
      height={1280}
    />
  );
};

export const MyComponent: React.FC = () => {
  const frame = useCurrentFrame();

  // Source video duration (~60s)
  const sourceDurationInFrames = 1802;

  // 120 BPM -> 1 beat every 15 frames at 30 fps
  const beatInterval = 15;

  // Calculate visual kick pulse (sharp attack, exponential decay)
  const frameInBeat = frame % beatInterval;
  const kickPulse = Math.max(0, 1 - frameInBeat / 7);

  const scale = 1 + kickPulse * 0.045;
  const glowColor = `rgba(255, 20, 100, ${kickPulse * 0.85})`;
  const borderWidth = Math.round(kickPulse * 16);

  return (
    <AbsoluteFill style={{ backgroundColor: "black", overflow: "hidden" }}>
      {/* Video Loop with Bass-Reactive Zoom and Neon Border Flash */}
      <div
        style={{
          width: "100%",
          height: "100%",
          transform: `scale(${scale})`,
          boxSizing: "border-box",
          border: `${borderWidth}px solid ${glowColor}`,
          boxShadow: `inset 0 0 40px ${glowColor}`,
        }}
      >
        <Loop durationInFrames={sourceDurationInFrames}>
          <OffthreadVideo
            src={staticFile('source_video.mp4')}
            style={{ width: "100%", height: "100%", objectFit: "cover" }}
          />
        </Loop>
      </div>

      {/* Optimized Single Continuous Kick Track Audio Overlay */}
      <Audio src={staticFile("kick_track.wav")} volume={0.9} />
    </AbsoluteFill>
  );
};
