// C5-REAL EXERGY CERTIFIED
import { AbsoluteFill, Composition, staticFile, Loop, OffthreadVideo } from "remotion";
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
  // Source video is ~60 seconds (1802 frames at 30 fps)
  const sourceDurationInFrames = 1802;

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Loop durationInFrames={sourceDurationInFrames}>
        <OffthreadVideo
          src={staticFile('source_video.mp4')}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </Loop>
    </AbsoluteFill>
  );
};
