// C5-REAL EXERGY CERTIFIED
import { AbsoluteFill, Audio, Sequence, useCurrentFrame, useVideoConfig, spring, OffthreadVideo, staticFile } from "remotion";
import script from "./script.json";

export const CortexVideo = () => {
  const { fps, width, height } = useVideoConfig();

  let currentStart = 0;

  return (
    <AbsoluteFill style={{ backgroundColor: "#000" }}>
      {/* Offthread B-Roll for background, required by SOTA */}
      <OffthreadVideo
        src="https://www.w3schools.com/html/mov_bbb.mp4"
        style={{ opacity: 0.3, width: '100%', height: '100%', objectFit: 'cover' }}
        muted
      />

      {script.map((scene, idx) => {
        const start = currentStart;
        const duration = scene.durationFrames;
        currentStart += duration;

        return (
          <Sequence key={idx} from={start} durationInFrames={duration}>
            <Audio src={staticFile(scene.audioFile)} />
            <SceneContent scene={scene} fps={fps} />
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};

const SceneContent = ({ scene, fps }) => {
  const frame = useCurrentFrame();

  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          gap: '20px',
          padding: '60px',
          background: 'rgba(20, 20, 20, 0.4)',
          backdropFilter: 'blur(20px)',
          WebkitBackdropFilter: 'blur(20px)',
          borderRadius: '24px',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          maxWidth: '80%',
        }}
      >
        {scene.timestamps.map((t, i) => {
          // Word sync micro-animation
          const isActive = frame >= t.startFrame && frame <= t.endFrame;
          const hasPassed = frame > t.endFrame;

          const scale = spring({
            fps,
            frame: frame - t.startFrame,
            config: { damping: 12, mass: 0.5 }
          });

          return (
            <span
              key={i}
              style={{
                fontSize: '72px',
                fontWeight: 'bold',
                fontFamily: 'system-ui, sans-serif',
                color: isActive ? '#fff' : (hasPassed ? 'rgba(255,255,255,0.7)' : 'rgba(255,255,255,0.3)'),
                transform: `scale(${isActive ? 1 + (scale * 0.1) : 1})`,
                transition: 'color 0.1s ease',
              }}
            >
              {t.word}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
