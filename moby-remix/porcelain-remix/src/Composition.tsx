// C5-REAL EXERGY CERTIFIED
import { Composition, Video, Audio, AbsoluteFill, staticFile } from "remotion";
import React from "react";

type Props = {};

export const MyComponent: React.FC<Props> = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <AbsoluteFill style={{
        filter: `saturate(1.5) contrast(1.2) hue-rotate(45deg)`, // static cosmic filter
      }}>
        <Video
          src={staticFile("remix_video.mp4")}
          style={{ width: "100%", height: "100%", objectFit: "cover" }}
        />
      </AbsoluteFill>
      <Audio src={staticFile("remix_audio_microtonal.mp3")} />

      {/* Title Overlay */}
      <AbsoluteFill style={{
        justifyContent: "center",
        alignItems: "center",
        pointerEvents: "none"
      }}>
        <h1 style={{
          fontFamily: "sans-serif",
          fontSize: 80,
          color: "rgba(255, 255, 255, 0.7)",
          textShadow: "0 0 40px rgba(255, 255, 255, 0.5)",
          letterSpacing: "0.2em",
          fontWeight: "lighter",
          mixBlendMode: "overlay"
        }}>
          PORCELAIN
        </h1>
        <h2 style={{
          fontFamily: "sans-serif",
          fontSize: 30,
          color: "rgba(255, 255, 255, 0.5)",
          letterSpacing: "0.5em",
          fontWeight: "lighter",
          mixBlendMode: "overlay"
        }}>
          MICROTONAL COSMIC DOWNTEMPO
        </h2>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

export const MyComposition = () => {
  return (
    <Composition
      id="MobyCosmicRemix"
      component={MyComponent}
      durationInFrames={5612} // approx 3:44.5 at 25fps
      fps={25}
      width={1280}
      height={720}
    />
  );
};
