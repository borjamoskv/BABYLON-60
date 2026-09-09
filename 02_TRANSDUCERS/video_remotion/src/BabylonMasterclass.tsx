import React from "react";
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate, Series } from "remotion";

export type MotionPhysics = {
  mass: number;
  damping: number;
  stiffness: number;
};

export type SceneData = {
  durationInFrames: number;
  text: string;
  physics: MotionPhysics;
};

export const Scene: React.FC<{ data: SceneData }> = ({ data }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const enterScale = spring({ fps, frame, config: data.physics });
  const opacity = spring({ fps, frame: frame - 5, config: { damping: 20 } });

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <h2 style={{ 
        transform: `scale(${enterScale})`, 
        opacity: opacity, 
        color: "#EDEDED", 
        fontSize: "60px", 
        textAlign: "center", 
        maxWidth: "1200px",
        fontFamily: "ui-monospace, monospace" 
      }}>
        {data.text}
      </h2>
    </AbsoluteFill>
  );
};

export const BabylonMasterclass: React.FC<{ 
  title: string; 
  sessionHash: string;
  scenes: SceneData[];
}> = ({ title, sessionHash, scenes = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const glowOpacity = interpolate(
    spring({ fps, frame: frame - 20, config: { damping: 10, stiffness: 40 } }),
    [0, 1], [0, 0.4]
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "#030303", overflow: "hidden" }}>
      <AbsoluteFill style={{
          backgroundImage: "linear-gradient(#111 1px, transparent 1px), linear-gradient(90deg, #111 1px, transparent 1px)",
          backgroundSize: "60px 60px", opacity: 0.5,
      }} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
         <div style={{ width: "800px", height: "400px", background: "radial-gradient(circle, rgba(255, 68, 68, 0.8) 0%, rgba(0,0,0,0) 70%)", opacity: glowOpacity, filter: "blur(80px)" }} />
      </AbsoluteFill>

      <AbsoluteFill style={{ top: "40px", left: "40px", color: "#FF4444", fontFamily: "monospace", fontSize: "24px" }}>
        {sessionHash} | {title}
      </AbsoluteFill>

      <AbsoluteFill style={{ zIndex: 10 }}>
        <Series>
          {scenes.map((scene, i) => (
            <Series.Sequence key={i} durationInFrames={scene.durationInFrames}>
              <Scene data={scene} />
            </Series.Sequence>
          ))}
        </Series>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
