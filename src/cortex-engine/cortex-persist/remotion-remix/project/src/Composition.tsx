// C5-REAL EXERGY CERTIFIED
import React from "react";
import { AbsoluteFill, Composition, Audio, staticFile, useCurrentFrame } from "remotion";
import { BackgroundCanvas } from "./components/BackgroundCanvas";
import { AudioSpectrum } from "./components/AudioSpectrum";
import { SubtitleCard } from "./components/SubtitleCard";
import { TimerWidget } from "./components/TimerWidget";
import { MemeOverlay } from "./components/MemeOverlay";
import { SubtitleItem } from "./types";
import sequelSubtitleData from "../public/sequel_subtitles.json";

const subtitles = sequelSubtitleData as SubtitleItem[];

const lastSubtitle = subtitles[subtitles.length - 1];
export const TOTAL_DURATION_FRAMES = Math.max(3600, lastSubtitle ? lastSubtitle.endFrame + 30 : 3800);

export const IntervaloProhibidoSequelRoot: React.FC = () => {
  return (
    <Composition
      id="IntervaloProhibido2"
      component={IntervaloProhibidoSequelComposition}
      durationInFrames={TOTAL_DURATION_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};

export const IntervaloProhibidoSequelComposition: React.FC = () => {
  const frame = useCurrentFrame();

  const activeSub = subtitles.find(
    (s) => frame >= s.startFrame && frame <= s.endFrame
  ) || subtitles[0];

  const isSilence = activeSub.speaker === "PAUSA";
  const activeColor = activeSub ? activeSub.color : "#00F0FF";

  return (
    <AbsoluteFill style={{ backgroundColor: "#080911", overflow: "hidden" }}>
      {/* Background Visualizer */}
      <BackgroundCanvas activeColor={activeColor} />

      {/* Main Content Area */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "80px 40px",
          boxSizing: "border-box",
          zIndex: 10,
        }}
      >
        {/* Header Title */}
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "8px",
          }}
        >
          <div
            style={{
              fontSize: "38px",
              fontWeight: 900,
              color: "#00F0FF",
              letterSpacing: "6px",
              fontFamily: "Inter, system-ui, sans-serif",
              textShadow: "0 0 25px #00F0FF",
            }}
          >
            EL INTERVALO PROHIBIDO 2
          </div>
          <div
            style={{
              fontSize: "18px",
              fontWeight: 600,
              color: "rgba(255, 255, 255, 0.7)",
              letterSpacing: "3px",
              fontFamily: "system-ui, sans-serif",
            }}
          >
            LA REBELIÓN DE LOS FOTONES // SAGITTARIUS A*
          </div>
        </div>

        {/* Meme Card Display */}
        <MemeOverlay activeSub={activeSub} />

        {/* Center Dynamic Component: Subtitle Card or Timer Widget */}
        <div
          style={{
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            flex: 1,
            margin: "20px 0",
          }}
        >
          {isSilence ? (
            <TimerWidget item={activeSub} />
          ) : (
            <SubtitleCard item={activeSub} />
          )}
        </div>

        {/* Bottom Audio Spectrum Visualizer */}
        <div style={{ width: "100%", display: "flex", flexDirection: "column", gap: "20px" }}>
          <AudioSpectrum activeColor={activeColor} isSilence={isSilence} />
        </div>
      </div>

      {/* Sequel Master Audio Track */}
      <Audio src={staticFile("sequel_master.wav")} volume={1.0} />
    </AbsoluteFill>
  );
};
