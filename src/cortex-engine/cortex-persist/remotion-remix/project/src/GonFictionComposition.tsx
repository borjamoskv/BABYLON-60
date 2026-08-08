// C5-REAL EXERGY CERTIFIED
import React from "react";
import { AbsoluteFill, Video, Audio, staticFile, useCurrentFrame, interpolate, spring } from "remotion";
import subtitleData from "../public/gon_fiction_subtitles.json";
import { SubtitleItem } from "./types";

const subtitles = subtitleData as SubtitleItem[];
const lastSubtitle = subtitles[subtitles.length - 1];
export const GON_FICTION_DURATION_FRAMES = lastSubtitle ? lastSubtitle.endFrame + 150 : 22200;

export const GonFictionComposition: React.FC = () => {
  const frame = useCurrentFrame();

  const activeSub = subtitles.find(
    (s) => frame >= s.startFrame && frame <= s.endFrame
  ) || null;

  const isSilence = activeSub === null || activeSub.speaker === "PAUSA";

  // Global Video Progress Bar (0 to 100%) - Tacky red bar at the bottom
  const globalProgress = interpolate(frame, [0, GON_FICTION_DURATION_FRAMES], [0, 100], {
    extrapolateLeft: "clamp",
    extrapolateRight: "clamp",
  });

  // Hyper-kinetic trig/spring animations for mouth & avatar physics
  const isSpeaking = !isSilence;

  // Cutre MS Paint bouncing
  const bounceY = isSpeaking ? Math.abs(Math.sin(frame * 0.8)) * -60 : 0;
  const squishX = isSpeaking ? 1.0 + Math.cos(frame * 1.5) * 0.2 : 1.0;
  const headRotation = isSpeaking ? Math.sin(frame * 0.5) * 20 : 0;

  // Spring animation for entrance when speaker changes
  const speakerEntrance = spring({
    fps: 30,
    frame: activeSub ? frame - activeSub.startFrame : 0,
    config: { damping: 8, stiffness: 100 }, // Bouncier!
  });

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "#FF00FF", // Magenta fallback
        overflow: "hidden",
        fontFamily: "'Comic Sans MS', Impact, sans-serif", // CHANANTE FONT
      }}
    >
      {/* 1. BACKGROUND: FFmpeg Chanante Render */}
      <Video
        src={staticFile("out_gon_fiction_8bit.mp4")}
        style={{ width: "100%", height: "100%", objectFit: "cover", opacity: 0.9 }}
      />

      {/* 2. CHEAP TV CHANNEL LOGO (Top Right) */}
      <div
        style={{
          position: "absolute",
          top: "40px",
          right: "40px",
          display: "flex",
          flexDirection: "column",
          alignItems: "flex-end",
          zIndex: 10,
        }}
      >
        <div
          style={{
            backgroundColor: "blue",
            color: "yellow",
            padding: "10px 20px",
            fontSize: "36px",
            fontWeight: "bold",
            borderRadius: "50%",
            border: "8px solid red",
            transform: `rotate(${Math.sin(frame * 0.1) * 10}deg)`,
            boxShadow: "10px 10px 0px black"
          }}
        >
          TELE<br/>BILBO
        </div>
      </div>

      {/* 2.5 NEWS TICKER CUTRE CHANANTE */}
      <div
        style={{
          position: "absolute",
          top: "160px",
          left: 0,
          right: 0,
          backgroundColor: "yellow",
          borderTop: "6px solid black",
          borderBottom: "6px solid black",
          color: "black",
          fontSize: "40px",
          fontWeight: "bold",
          padding: "5px 0",
          overflow: "hidden",
          whiteSpace: "nowrap",
          zIndex: 15,
          boxShadow: "0 10px 0px black",
        }}
      >
        <div
          style={{
            transform: `translateX(${(frame * -10) % 3000 + 1080}px)`,
          }}
        >
          ÚLTIMA HORA: EL KERNEL SE HA IDO DE BARETOS... AY VA QUÉ CHORRAZO... SE BUSCA GAMBITERO POR BILBAO LA VIEJA... ERES UN REGULERO... HIJO DE P. HAY QUE DECIRLO MÁS... A TOPE DE POWER...
        </div>
      </div>

      {/* 2.6 RANDOM FLOATING CHANANTE TEXT (Aparece y desaparece estroboscópicamente) */}
      {Math.sin(frame * 0.2) > 0.8 && (
        <div
          style={{
            position: "absolute",
            top: `${Math.abs(Math.sin(frame * 0.1)) * 50 + 20}%`,
            left: `${Math.abs(Math.cos(frame * 0.15)) * 50 + 10}%`,
            color: "#00FF00",
            fontSize: "80px",
            fontFamily: "Impact, sans-serif",
            WebkitTextStroke: "4px black",
            textShadow: "8px 8px 0px black",
            transform: `rotate(${Math.sin(frame * 0.5) * 45}deg)`,
            zIndex: 12,
          }}
        >
          ¡A TOPE DE POWER!
        </div>
      )}

      {Math.cos(frame * 0.15) > 0.9 && (
        <div
          style={{
            position: "absolute",
            top: `${Math.abs(Math.cos(frame * 0.2)) * 60 + 10}%`,
            right: `${Math.abs(Math.sin(frame * 0.1)) * 40 + 10}%`,
            color: "magenta",
            fontSize: "90px",
            fontFamily: "'Comic Sans MS', sans-serif",
            WebkitTextStroke: "3px white",
            textShadow: "5px 5px 0px black",
            transform: `rotate(${Math.cos(frame * 0.4) * -30}deg)`,
            zIndex: 12,
          }}
        >
          BOCACHANCO
        </div>
      )}

      {/* 3. SUBTITLE / DIALOGUE & AVATAR LAYER */}
      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "flex-end",
          padding: "80px 40px 180px 40px",
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
              gap: "10px",
              width: "100%",
              transform: `scale(${speakerEntrance})`,
              opacity: interpolate(speakerEntrance, [0, 1], [0, 1]),
            }}
          >
            {/* CHEAP AVATAR BOUNCING */}
            <div
              style={{
                position: "relative",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                transform: `translateY(${bounceY}px) rotate(${headRotation}deg) scaleX(${squishX})`,
              }}
            >
              {/* Avatar Emoji Container */}
              <div
                style={{
                  fontSize: "180px",
                  filter: `drop-shadow(15px 15px 0px black)`,
                  zIndex: 2,
                }}
              >
                {activeSub.avatar}
              </div>
            </div>

            {/* SPEAKER NAME BADGE (Comic Sans, absurd colors) */}
            <div
              style={{
                fontSize: "40px",
                fontWeight: "bold",
                color: "white",
                backgroundColor: activeSub.color,
                padding: "10px 30px",
                border: "6px solid black",
                boxShadow: "8px 8px 0px black",
                transform: "rotate(-3deg)",
                marginBottom: "20px",
              }}
            >
              {activeSub.speaker}
            </div>

            {/* TEXT DIALOGUE BOX (Impact Meme Style) */}
            <div
              style={{
                width: "90%",
                textAlign: "center",
              }}
            >
              <div
                style={{
                  fontSize: "65px",
                  lineHeight: "1.2",
                  color: "yellow",
                  fontFamily: "Impact, sans-serif",
                  textTransform: "uppercase",
                  WebkitTextStroke: "4px black",
                  textShadow: "6px 6px 0px black",
                }}
              >
                {activeSub.text}
              </div>
            </div>
          </div>
        )}

        {/* PAUSE / SILENCE DISPLAY */}
        {isSilence && (
          <div
            style={{
              backgroundColor: "magenta",
              border: "10px dotted yellow",
              padding: "40px 60px",
              color: "white",
              fontSize: "50px",
              fontFamily: "Comic Sans MS, sans-serif",
              fontWeight: "bold",
              textShadow: "4px 4px 0px black",
              boxShadow: "15px 15px 0px black",
              marginBottom: "150px",
              transform: `rotate(${Math.sin(frame * 0.2) * 5}deg)`,
            }}
          >
            ESPERA UN REGULÍN...
          </div>
        )}
      </div>

      {/* 4. TACKY BOTTOM PROGRESS BAR */}
      <div
        style={{
          position: "absolute",
          bottom: "30px",
          left: "20px",
          right: "20px",
          height: "20px",
          backgroundColor: "white",
          border: "4px solid black",
          zIndex: 20,
        }}
      >
        <div
          style={{
            height: "100%",
            width: `${globalProgress}%`,
            backgroundColor: "red",
          }}
        />
      </div>

      {/* 5. MASTER AUDIO TRACK */}
      <Audio src={staticFile("gon_fiction_master.wav")} volume={1.0} />
    </AbsoluteFill>
  );
};
