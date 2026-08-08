// C5-REAL EXERGY CERTIFIED
import { AbsoluteFill, Audio, useCurrentFrame, useVideoConfig, spring, interpolate, Video, staticFile } from "remotion";
import React, { useMemo } from "react";
import subtitles from "../../public/legion_subtitles.json";

// SOTA GLASSMORPHISM AESTHETICS

const SotaContainer: React.CSSProperties = {
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  justifyContent: "flex-end",
  height: "100%",
  width: "100%",
  paddingBottom: "250px",
  fontFamily: "'Inter', 'Outfit', sans-serif",
};

const GlassPanel: React.CSSProperties = {
  background: "rgba(10, 15, 30, 0.7)",
  backdropFilter: "blur(32px)",
  WebkitBackdropFilter: "blur(32px)",
  border: "1px solid rgba(255, 255, 255, 0.1)",
  borderTop: "1px solid rgba(255, 255, 255, 0.3)",
  borderRadius: "40px",
  padding: "60px 80px",
  width: "85%",
  display: "flex",
  flexDirection: "column",
  alignItems: "center",
  boxShadow: "0 40px 80px rgba(0, 0, 0, 0.8), inset 0 2px 20px rgba(255, 255, 255, 0.05)",
};

const AvatarWrapper: React.CSSProperties = {
  position: "absolute",
  top: "-80px",
  width: "160px",
  height: "160px",
  borderRadius: "50%",
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  fontSize: "80px",
  background: "linear-gradient(135deg, rgba(40,40,60,0.9), rgba(10,10,20,0.9))",
  boxShadow: "0 20px 40px rgba(0,0,0,0.5), inset 0 2px 5px rgba(255,255,255,0.2)",
};

const NameTag: React.CSSProperties = {
  fontSize: "32px",
  fontWeight: 900,
  letterSpacing: "6px",
  textTransform: "uppercase",
  marginTop: "40px",
  marginBottom: "30px",
  textShadow: "0 4px 12px rgba(0,0,0,0.8)",
};

const SubtitleText: React.CSSProperties = {
  fontSize: "52px",
  fontWeight: 500,
  color: "#FFFFFF",
  textAlign: "center",
  lineHeight: 1.4,
  textShadow: "0 4px 16px rgba(0,0,0,0.6)",
};

const HeaderBar: React.CSSProperties = {
  position: "absolute",
  top: "80px",
  left: "8%",
  right: "8%",
  display: "flex",
  justifyContent: "space-between",
  alignItems: "center",
  background: "rgba(0,0,0,0.4)",
  backdropFilter: "blur(12px)",
  padding: "20px 40px",
  borderRadius: "100px",
  border: "1px solid rgba(255,255,255,0.1)",
};

const KernelStatusText: React.CSSProperties = {
  color: "#00F0FF",
  fontSize: "28px",
  fontWeight: 700,
  letterSpacing: "3px",
  textTransform: "uppercase",
};

const C5Logo: React.CSSProperties = {
  color: "#FFFFFF",
  fontSize: "32px",
  fontWeight: 900,
  letterSpacing: "2px",
};

const SceneSubtitle = ({ sub, frame, fps }: { sub: any; frame: number; fps: number }) => {
  const localFrame = frame - sub.startFrame;
  const duration = sub.endFrame - sub.startFrame;

  // SOTA micro-animations: smooth spring entry
  const entrance = spring({
    frame: localFrame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8 },
  });

  const exit = spring({
    frame: duration - localFrame,
    fps,
    config: { damping: 14, stiffness: 120, mass: 0.8 },
  });

  const scale = Math.min(entrance, exit);
  const opacity = Math.min(
    interpolate(localFrame, [0, 10], [0, 1], { extrapolateRight: "clamp" }),
    interpolate(duration - localFrame, [0, 10], [0, 1], { extrapolateRight: "clamp" })
  );
  const translateY = interpolate(scale, [0, 1], [40, 0]);

  // Dynamic glow based on the character's designated color
  const glowShadow = `0 0 30px ${sub.color}80`;
  const borderHighlight = `2px solid ${sub.color}`;

  return (
    <div style={{ ...SotaContainer, opacity }}>
      <div
        style={{
          ...GlassPanel,
          transform: `scale(${scale}) translateY(${translateY}px)`,
          boxShadow: `${GlassPanel.boxShadow}, ${glowShadow}`,
        }}
      >
        <div style={{ ...AvatarWrapper, border: borderHighlight }}>
          {sub.avatar}
        </div>
        <div style={{ ...NameTag, color: sub.color }}>{sub.speaker}</div>
        <div style={{ ...SubtitleText }}>{sub.text}</div>
      </div>
    </div>
  );
};

export const LegionComposition: React.FC = () => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Find the currently active subtitle
  const activeSub = useMemo(() => {
    return subtitles.find((s: any) => frame >= s.startFrame && frame < s.endFrame);
  }, [frame]);

  // Gentle pulsing for the header
  const headerPulse = interpolate(
    Math.sin(frame / 15),
    [-1, 1],
    [0.8, 1]
  );

  return (
    <AbsoluteFill style={{ backgroundColor: "black" }}>
      <Video src={staticFile("out_sota_legion.mp4")} />

      <AbsoluteFill>
        <div style={{ ...HeaderBar, opacity: headerPulse }}>
          <div style={C5Logo}>C5-REAL LEGION</div>
          <div style={KernelStatusText}>KERNEL: ONLINE</div>
        </div>

        {activeSub && <SceneSubtitle sub={activeSub} frame={frame} fps={fps} />}
      </AbsoluteFill>
      <Audio src={"/legion_master.wav"} />
    </AbsoluteFill>
  );
};

// Compute the total duration directly from subtitles data
export const LEGION_DURATION_FRAMES = subtitles.length > 0
  ? Math.max(...subtitles.map((s: any) => s.endFrame)) + 30
  : 3000;
