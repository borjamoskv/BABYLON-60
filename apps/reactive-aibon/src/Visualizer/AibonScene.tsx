import { useWindowedAudioData, visualizeAudio } from "@remotion/media-utils";
import React, { useMemo } from "react";
import { AbsoluteFill, Audio, Img, spring, staticFile, useCurrentFrame, useVideoConfig } from "remotion";

interface AibonSceneProps {
  audioSrc: string;
}

const TOTAL_IMAGES = 53;

const IMAGES = Array.from({ length: TOTAL_IMAGES }, (_, i) => staticFile(`media/batch_${i}.jpg`));

const CAPTIONS = [
  "¡¡YO SOY EL AIBON!!",
  "¡¡EL PUTO AIBON!!",
  "CHEK! CHEK! CHEKIO!",
  "BRUTAL.",
  "THE MATH... NEVER ADDS UP",
  "THIS IS UNDER CONTROL",
  "EVERYTHING IS ALREADY BURNT.",
  "LEGENDS OF THE LAST SPREE",
  "MARVEL AIBON CINEMATIC UNIVERSE"
];

const ONOMATOPOEIA = ["POW!", "KBOOM!", "CHEKIO!", "BRUTAL!", "AIBON!", "BAM!", "BOOM!"];

export const AibonScene: React.FC<AibonSceneProps> = ({ audioSrc }) => {
  const { fps, width, height } = useVideoConfig();
  const frame = useCurrentFrame();

  const { audioData, dataOffsetInSeconds } = useWindowedAudioData({
    src: audioSrc,
    frame,
    fps,
    windowInSeconds: 2,
  });

  if (!audioData) {
    return null;
  }

  const values = visualizeAudio({
    audioData,
    fps,
    frame,
    optimizeFor: "speed",
    numberOfSamples: 64,
    dataOffsetInSeconds,
  });

  // Dividimos frecuencias (Fourier BFT)
  const bass = values.slice(0, 4).reduce((a, b) => a + b, 0) / 4;
  const snare = values.slice(12, 16).reduce((a, b) => a + b, 0) / 4;
  const hihat = values.slice(48, 64).reduce((a, b) => a + b, 0) / 16;
  const vocalFreq = values.slice(8, 24).reduce((a, b) => a + b, 0) / 16;

  // Beat Detection
  const isKick = bass > 0.35;
  const isSnare = snare > 0.25;

  // Marvel Comic Spring Physics
  const bounceSpring = spring({
    fps,
    frame: frame % 10,
    config: { damping: 8, mass: 0.3, stiffness: 160 }
  });

  // Marvel Action Pop Spring
  const popSpring = spring({
    fps,
    frame: isKick ? frame % 8 : 0,
    config: { damping: 6, mass: 0.2, stiffness: 200 }
  });

  // Voiceover Intro Spring (Antonio Gallo Style)
  const isIntro = frame < 90;
  const introSpring = spring({
    fps,
    frame,
    config: { damping: 10, mass: 0.4, stiffness: 140 }
  });

  // Camera 3D Dynamics
  const cameraRotX = Math.sin(frame * 0.05) * 5;
  const cameraRotY = Math.cos(frame * 0.04) * 7;
  const cameraZoom = 1 + (isKick ? bass * 0.16 : 0);

  // SLIDESHOW LOGIC (Ken Burns + Hard Cuts)
  const framesPerSlide = 40; // Change photo every 40 frames (~1.3 seconds)
  const frameInSlide = frame % framesPerSlide;
  const slideIndex = Math.floor(frame / framesPerSlide);
  
  const imgIndex1 = slideIndex % TOTAL_IMAGES;
  const imgIndex2 = (slideIndex + 3) % TOTAL_IMAGES; // Background photo

  // Ken Burns zoom (1.0 to 1.15 over the duration of the slide)
  const kenBurnsScale = 1 + (frameInSlide / framesPerSlide) * 0.15;

  const captionIndex = Math.floor(frame / 35) % CAPTIONS.length;
  const currentCaption = CAPTIONS[captionIndex];

  const onomatopoeiaIndex = Math.floor(frame / 12) % ONOMATOPOEIA.length;
  const currentOnomatopoeia = ONOMATOPOEIA[onomatopoeiaIndex];

  // 32-Bar Realtime Equalizer values
  const equalizerBars = values.slice(0, 32);

  // Marvel End Credits trigger (Final 350 frames ~ 11.6 seconds)
  const isEndCredits = frame >= 12150;
  const endCreditsFrame = frame - 12150;
  const creditsSpring = spring({
    fps,
    frame: endCreditsFrame,
    config: { damping: 12, mass: 0.5, stiffness: 100 }
  });

  return (
    <AbsoluteFill style={{ 
      backgroundColor: "#0b0507", 
      overflow: "hidden",
      perspective: "1200px" 
    }}>
      {/* VOICE OVER AUDIO INTRO (ANTONIO GALLO STYLE) */}
      <Audio src={staticFile("intro.wav")} />

      {/* CAMERA 3D PARALLAX CONTAINER */}
      <AbsoluteFill style={{
        transform: `scale(${cameraZoom}) rotateX(${cameraRotX}deg) rotateY(${cameraRotY}deg)`,
        transformStyle: "preserve-3d",
        filter: isKick ? "drop-shadow(6px 6px 0px #e62429) drop-shadow(-6px -6px 0px #fbb03b)" : "none",
        transition: "transform 0.03s ease-out"
      }}>
        {/* CIELO REACTIVO MARVEL RED & GOLD */}
        <AbsoluteFill
          style={{
            background: `radial-gradient(circle at 50% 30%, rgba(230, 36, 41, ${0.4 + hihat * 2}), rgba(251, 176, 59, ${bass * 0.8}), #0b0507)`,
            transform: "translateZ(-600px) scale(1.6)"
          }}
        />

        {/* MARVEL ANAMORPHIC BLUE LENS FLARES */}
        <div style={{
          position: "absolute",
          top: "30%",
          left: 0,
          right: 0,
          height: "8px",
          background: `linear-gradient(90deg, transparent, #00d2ff, #ffffff, #00d2ff, transparent)`,
          transform: `translateZ(-500px) translateY(${Math.sin(frame * 0.12) * 140}px)`,
          boxShadow: "0 0 35px #00d2ff",
          opacity: isSnare ? 0.95 : 0.2
        }} />

        {/* BACKGROUND PHOTO (Blurred) */}
        <AbsoluteFill style={{ 
          transform: `translateZ(-300px) scale(${1.3 + (isSnare ? snare * 0.3 : 0)})`,
          opacity: 0.4,
          filter: "blur(15px)",
          alignItems: "center",
          justifyContent: "center",
          zIndex: 1
        }}>
          <Img src={IMAGES[imgIndex2]} style={{ width: "120%", height: "120%", objectFit: "cover" }} />
        </AbsoluteFill>

        {/* MAIN SLIDESHOW PHOTO (Ken Burns) */}
        <AbsoluteFill style={{
          transform: `translateZ(50px) scale(${kenBurnsScale + (isKick ? bass * 0.1 : 0)})`,
          alignItems: "center",
          justifyContent: "center",
          zIndex: 5
        }}>
          <Img src={IMAGES[imgIndex1]} style={{ 
            height: "80%", 
            border: "12px solid #e62429", 
            borderRadius: 20,
            boxShadow: "0 30px 60px rgba(0,0,0,0.8), 0 0 40px rgba(230,36,41,0.5)"
          }} />
        </AbsoluteFill>

        {/* ANTONIO GALLO INTRO VOICE OVER SPEECH BANNER */}
        {isIntro && (
          <div style={{
            position: "absolute",
            left: "50%",
            top: "22%",
            transform: `translate3d(-50%, 0, 450px) scale(${introSpring}) rotate(-3deg)`,
            backgroundColor: "#fbb03b",
            color: "#e62429",
            fontFamily: "Impact, sans-serif",
            fontSize: 56,
            padding: "16px 45px",
            borderRadius: 20,
            border: "6px solid #000",
            boxShadow: "12px 12px 0px #000, 0 0 50px #fbb03b",
            textShadow: "3px 3px 0px #fff",
            zIndex: 35,
            textAlign: "center"
          }}>
            "Pero, ¿quién cojones es el Aibon?"
          </div>
        )}

        {/* MARVEL COMIC ONOMATOPOEIA POPUP (POW! KBOOM! CHEKIO!) */}
        {isKick && !isEndCredits && !isIntro && (
          <div style={{
            position: "absolute",
            right: "15%",
            top: "20%",
            transform: `translate3d(0, 0, 400px) scale(${1 + popSpring * 0.8}) rotate(-12deg)`,
            backgroundColor: "#fbb03b",
            color: "#e62429",
            fontFamily: "Impact, sans-serif",
            fontSize: 64,
            padding: "10px 30px",
            border: "5px solid #000",
            boxShadow: "8px 8px 0px #000",
            textShadow: "3px 3px 0px #fff",
            zIndex: 25
          }}>
            {currentOnomatopoeia}
          </div>
        )}

        {/* KINETIC TYPOGRAPHY CAPTION HUD (MARVEL COMIC TITLE STYLE) */}
        {!isEndCredits && !isIntro && (
          <div style={{
            position: "absolute",
            left: "50%",
            bottom: "14%",
            transform: `translate3d(-50%, 0, 200px) scale(${1 + (bounceSpring * 0.35) + (isSnare ? snare * 0.6 : 0)})`,
            backdropFilter: "blur(25px)",
            backgroundColor: "#e62429",
            color: "#fff",
            fontFamily: "Impact, sans-serif",
            fontSize: 52,
            letterSpacing: 6,
            textTransform: "uppercase",
            padding: "14px 45px",
            borderRadius: 15,
            border: "4px solid #fbb03b",
            boxShadow: "8px 8px 0px #000, 0 0 40px rgba(230, 36, 41, 0.8)",
            textShadow: "3px 3px 0px #000, -2px -2px 0px #fbb03b",
            zIndex: 20
          }}>
            {currentCaption}
          </div>
        )}

        {/* 32-BAR FFT SPECTRUM EQUALIZER (GOLD & RED NEON) */}
        <div style={{
          position: "absolute",
          bottom: "2%",
          left: "8%",
          right: "8%",
          height: 90,
          display: "flex",
          alignItems: "flex-end",
          justifyContent: "space-between",
          transform: "translateZ(250px)",
          zIndex: 22
        }}>
          {equalizerBars.map((val, idx) => (
            <div
              key={idx}
              style={{
                width: "2.6%",
                height: `${Math.min(100, Math.max(10, val * 240))}%`,
                background: idx % 2 === 0 ? "linear-gradient(to top, #e62429, #ff5252)" : "linear-gradient(to top, #fbb03b, #ffee55)",
                borderRadius: "4px 4px 0 0",
                boxShadow: "0 0 14px rgba(251, 176, 59, 0.8)",
                transition: "height 0.03s ease-out"
              }}
            />
          ))}
        </div>

        {/* MARVEL COMIC HALFTONE DOT OVERLAY */}
        <AbsoluteFill style={{
          backgroundImage: "radial-gradient(rgba(0, 0, 0, 0.4) 20%, transparent 20%)",
          backgroundSize: "8px 8px",
          pointerEvents: "none",
          zIndex: 30
        }} />

        {/* MARVEL END CREDITS OVERLAY CARD */}
        {isEndCredits && (
          <AbsoluteFill style={{
            backgroundColor: "rgba(11, 5, 7, 0.95)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            transform: `translateZ(500px) scale(${creditsSpring})`,
            zIndex: 40,
            padding: 40
          }}>
            <div style={{
              border: "6px solid #fbb03b",
              backgroundColor: "#e62429",
              padding: "20px 60px",
              borderRadius: 20,
              boxShadow: "0 0 60px #e62429, 12px 12px 0px #000",
              textAlign: "center",
              marginBottom: 30
            }}>
              <h1 style={{
                fontFamily: "Impact, sans-serif",
                fontSize: 80,
                color: "#fbb03b",
                margin: 0,
                letterSpacing: 8,
                textShadow: "4px 4px 0px #000"
              }}>
                BORJA MOSKV
              </h1>
              <h2 style={{
                fontFamily: "Impact, sans-serif",
                fontSize: 54,
                color: "#ffffff",
                margin: 0,
                letterSpacing: 6,
                textShadow: "3px 3px 0px #000"
              }}>
                EL PUTO AIBON
              </h2>
            </div>

            <div style={{
              color: "#fff",
              fontFamily: "Impact, sans-serif",
              fontSize: 32,
              letterSpacing: 3,
              textAlign: "center",
              lineHeight: 1.8,
              textShadow: "2px 2px 0px #000"
            }}>
              <p style={{ margin: "5px 0", color: "#fbb03b" }}>DIRECTED & ORCHESTRATED BY: <span style={{ color: "#fff" }}>BORJA MOSKV</span></p>
              <p style={{ margin: "5px 0", color: "#fbb03b" }}>EXECUTIVE PRODUCERS: <span style={{ color: "#fff" }}>100 SOVEREIGN BFT AGENTS</span></p>
              <p style={{ margin: "5px 0", color: "#fbb03b" }}>MUSIC & AUDIO MASTERING: <span style={{ color: "#fff" }}>EL PUTO AIBON</span></p>
              <p style={{ margin: "5px 0", color: "#fbb03b" }}>VISUAL ENGINE: <span style={{ color: "#fff" }}>CHEMICAL BROTHERS × MARVEL CINEMATIC UNIVERSE</span></p>
            </div>
          </AbsoluteFill>
        )}

        {/* FLASH STROBE DEL TREN */}
        <AbsoluteFill
          style={{
            opacity: isKick ? 0.45 : 0,
            backgroundColor: "white",
            mixBlendMode: "overlay",
            transition: "opacity 0.03s",
            zIndex: 25
          }}
        />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
