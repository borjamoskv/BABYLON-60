// C5-REAL EXERGY CERTIFIED
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
  Audio,
  interpolate,
} from "remotion";
import { useAudioData, visualizeAudio } from "@remotion/media-utils";
import React from "react";

export const HouseVisualizer: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const audioFile = staticFile("house_track.wav");
  const audioData = useAudioData(audioFile);

  if (!audioData) {
    return null;
  }

  const numBars = 64;
  const visualizerData = visualizeAudio({
    fps,
    frame,
    audioData,
    numberOfSamples: numBars,
  });

  const globalIntensity =
    visualizerData.reduce((acc, curr) => acc + curr, 0) / numBars;
  const scale = interpolate(globalIntensity, [0, 0.5], [1, 1.15], {
    extrapolateRight: "clamp",
  });

  const chromaticOffset = interpolate(globalIntensity, [0, 0.5], [0, 15], {
    extrapolateRight: "clamp",
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#0A0A0A",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden",
      }}
    >
      <Audio src={audioFile} />

      <AbsoluteFill
        style={{
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
        }}
      >
        <div
          style={{
            width: 1000,
            height: 1000,
            borderRadius: "50%",
            border: "4px solid rgba(43, 59, 229, 0.3)",
            transform: `scale(${interpolate(globalIntensity, [0, 0.5], [1, 1.5])})`,
            opacity: interpolate(globalIntensity, [0, 0.5], [0.1, 0.5]),
            boxShadow: "0 0 100px #2B3BE5",
          }}
        />
        <div
          style={{
            position: "absolute",
            width: 800,
            height: 800,
            borderRadius: "50%",
            border: "2px solid rgba(236, 72, 153, 0.5)",
            transform: `scale(${interpolate(globalIntensity, [0, 0.3], [1, 1.3])})`,
            opacity: interpolate(globalIntensity, [0, 0.5], [0.2, 0.8]),
          }}
        />

        <Img
          src={staticFile("ufo_tattoo_vector.svg")}
          style={{
            position: "absolute",
            width: 150,
            height: 150,
            left: 200,
            top: 200,
            transform: `translateY(${Math.sin(frame * 0.1) * 20}px) rotate(${frame * 0.5}deg)`,
            opacity: interpolate(globalIntensity, [0, 0.5], [0.3, 0.9]),
            filter: "drop-shadow(0 0 10px #2B3BE5)",
          }}
        />
        <Img
          src={staticFile("ufo_tattoo_vector.svg")}
          style={{
            position: "absolute",
            width: 100,
            height: 100,
            right: 250,
            bottom: 300,
            transform: `translateY(${Math.cos(frame * 0.1) * 30}px) rotate(${-frame * 0.8}deg)`,
            opacity: interpolate(globalIntensity, [0, 0.5], [0.3, 0.9]),
            filter: "drop-shadow(0 0 10px #EC4899)",
          }}
        />
      </AbsoluteFill>

      <div
        style={{
          position: "relative",
          transform: `scale(${scale}) rotate(${frame * 0.05}deg)`,
        }}
      >
        <Img
          src={staticFile("frame_001.png")}
          style={{
            width: 600,
            height: 600,
            objectFit: "cover",
            borderRadius: "300px",
            boxShadow: `0 0 40px #EC4899`,
            border: "8px solid #2B3BE5",
          }}
        />
        <Img
          src={staticFile("frame_001.png")}
          style={{
            position: "absolute",
            top: 0,
            left: chromaticOffset,
            width: 600,
            height: 600,
            objectFit: "cover",
            borderRadius: "300px",
            mixBlendMode: "screen",
            filter: "sepia(100%) hue-rotate(300deg) saturate(1000%)",
            opacity: 0.6,
          }}
        />
        <Img
          src={staticFile("frame_001.png")}
          style={{
            position: "absolute",
            top: 0,
            left: -chromaticOffset,
            width: 600,
            height: 600,
            objectFit: "cover",
            borderRadius: "300px",
            mixBlendMode: "screen",
            filter: "sepia(100%) hue-rotate(180deg) saturate(1000%)",
            opacity: 0.6,
          }}
        />
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 100,
          display: "flex",
          flexDirection: "row",
          alignItems: "flex-end",
          gap: "6px",
          width: "100%",
          justifyContent: "center",
        }}
      >
        {visualizerData.map((v, i) => {
          const barHeight = v * 400;
          return (
            <div
              key={i}
              style={{
                width: 14,
                height: Math.max(8, barHeight),
                backgroundColor: i % 2 === 0 ? "#2B3BE5" : "#EC4899",
                borderRadius: 7,
                boxShadow: `0 0 15px ${i % 2 === 0 ? "#2B3BE5" : "#EC4899"}`,
              }}
            />
          );
        })}
      </div>

      <div
        style={{
          position: "absolute",
          top: 80,
          left: 80,
          fontFamily: "sans-serif",
          color: "white",
          textTransform: "uppercase",
          letterSpacing: "0.1em",
        }}
      >
        <h1
          style={{
            margin: 0,
            fontSize: "3rem",
            textShadow: "0 0 20px #2B3BE5",
          }}
        >
          MOSKV-1 // CLAUDE SCIENCE HOUSE
        </h1>
        <h2
          style={{
            margin: "10px 0 0 0",
            fontSize: "1.5rem",
            color: "#EC4899",
            textShadow: "0 0 10px #EC4899",
          }}
        >
          UFO HARMONICS // 128 BPM C5-REAL
        </h2>
      </div>

      <div
        style={{
          position: "absolute",
          bottom: 40,
          left: 80,
          fontFamily: "monospace",
          color: "rgba(255, 255, 255, 0.5)",
          fontSize: "1.2rem",
        }}
      >
        FRAME: {frame.toString().padStart(4, "0")} // SIGNAL
      </div>
    </AbsoluteFill>
  );
};
