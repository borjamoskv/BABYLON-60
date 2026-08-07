// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, spring, useVideoConfig, interpolate, Img, staticFile } from "remotion";
import { SubtitleItem } from "../types";

const MEME_FILES_BY_SPEAKER: Record<string, string> = {
  CHICOTE: "memes/chicote_kv_cache.svg",
  RAMONCIN: "memes/frusciante_kamehameha.svg",
  FRUSCIANTE: "memes/frusciante_kamehameha.svg",
  FLEA: "memes/flea_slap_bass.svg",
  HERMENEGILDO: "memes/hermenegildo_altozano.svg",
  EL_NOTA: "memes/the_dude_escohotado.svg",
  ESCOHOTADO: "memes/the_dude_escohotado.svg",
  CARL_COX: "memes/carl_cox_brian_cox.svg",
  BLAN_COX: "memes/carl_cox_brian_cox.svg",
};

export const MemeOverlay: React.FC<{ activeSub: SubtitleItem }> = ({ activeSub }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const memePath = MEME_FILES_BY_SPEAKER[activeSub.speaker];
  if (!memePath) return null;

  // Spring entrance animation
  const localFrame = Math.max(0, frame - activeSub.startFrame);
  const scale = spring({
    frame: localFrame,
    fps,
    config: { damping: 13, stiffness: 130 },
  });

  const rotate = interpolate(
    Math.sin(localFrame * 0.08),
    [-1, 1],
    [-2, 2]
  );

  return (
    <div
      style={{
        transform: `scale(${scale}) rotate(${rotate}deg)`,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        width: "90%",
        marginBottom: "16px",
      }}
    >
      <Img
        src={staticFile(memePath)}
        style={{
          width: "100%",
          maxHeight: "360px",
          objectFit: "contain",
          borderRadius: "16px",
          boxShadow: `0 0 35px ${activeSub.color}88, 0 12px 40px rgba(0,0,0,0.85)`,
        }}
      />
    </div>
  );
};
