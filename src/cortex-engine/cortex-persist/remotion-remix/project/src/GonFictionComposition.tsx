// C5-REAL EXERGY CERTIFIED
import React, from "react";
import { AbsoluteFill, Composition, Video, Audio, staticFile, useCurrentFrame, interpolate, spring } from "remotion";
import subtitleData from "../public/gon_fiction_subtitles.json";
import { SubtitleItem } from "./types";

const subtitles = subtitleData as SubtitleItem[];
const lastSubtitle = subtitles[subtitles.length - 1];
// The master audio is ~12:20, around 22200 frames.
export const GON_FICTION_DURATION_FRAMES = lastSubtitle ? lastSubtitle.endFrame + 150 : 22200;

export const GonFictionComposition: React.FC = () => {
  const frame = useCurrentFrame();

  const activeSub = subtitles.find(
    (s) => frame >= s.startFrame && frame <= s.endFrame
  ) || null;

  const isSilence = activeSub === null || activeSub.speaker === "PAUSA";

  // Lip-sync mock (bouncing avatar using frame interpolation to simulate speaking)
  // Real implementation would use getAudioData from @remotion/media-utils,
  // but to avoid network sandbox blocks with npm install, we use a trigonometric mock.
  const isSpeaking = !isSilence;
  const mouthOpenness = isSpeaking ? (Math.sin(frame * 0.8) > 0 ? 1.2 : 0.9) : 1.0;
  const avatarScale = spring({ fps: 30, frame, config: { damping: 10 } });

  // Map speakers to their avatars (row sprites or fallback emoji)
  const renderAvatar = (item: SubtitleItem) => {
    if (!item) return null;
    return (
      <div style={{
        fontSize: "120px",
        transform: `scale(${mouthOpenness})`,
        transition: "transform 50ms ease-out",
        filter: `drop-shadow(0px 0px 20px ${item.color})`
      }}>
        {item.avatar}
      </div>
    );
  };

  return (
    <AbsoluteFill style={{ backgroundColor: "#020005", overflow: "hidden" }}>
      {/* BACKGROUND: FFmpeg Kinetic 8-Bit Engine output */}
      <Video
        src={staticFile("out_gon_fiction_8bit.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.8 }}
      />

      {/* FOREGROUND: Remotion Text & Avatars */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          padding: "100px 40px",
          boxSizing: "border-box",
          zIndex: 10,
        }}
      >
        {activeSub && !isSilence && (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: "40px",
              marginTop: "auto",
              marginBottom: "300px"
            }}
          >
            {/* AVATAR + LIP SYNC */}
            {renderAvatar(activeSub)}

            {/* SPEAKER NAME */}
            <div style={{
              fontSize: "42px",
              fontWeight: 900,
              fontFamily: '"Press Start 2P", monospace, sans-serif',
              color: activeSub.color,
              textTransform: "uppercase",
              textShadow: "4px 4px 0px #000, 0px 0px 20px " + activeSub.color,
              letterSpacing: "4px",
            }}>
              [{activeSub.speaker}]
            </div>

            {/* TYPOGRAPHY / DIALOGUE */}
            <div style={{
              fontSize: "58px",
              fontWeight: 800,
              fontFamily: "Inter, system-ui, sans-serif",
              color: "#FFFFFF",
              textAlign: "center",
              lineHeight: "1.2",
              textShadow: "0px 6px 15px rgba(0,0,0,0.8)",
              background: "rgba(0,0,0,0.6)",
              padding: "30px 50px",
              borderRadius: "20px",
              border: `4px solid ${activeSub.color}`,
              boxShadow: `0 0 30px ${activeSub.color}50`
            }}>
              {activeSub.text}
            </div>
          </div>
        )}
      </div>

      {/* MASTER AUDIO */}
      <Audio src={staticFile("gon_fiction_master.wav")} volume={1.0} />
    </AbsoluteFill>
  );
};
