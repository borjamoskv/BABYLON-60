// C5-REAL EXERGY CERTIFIED
import React from "react";
import { Composition } from "remotion";
import { DocumentaryMain } from "./DocumentaryMain";
import scriptData from "./script.json";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="DocumentaryMain"
        component={DocumentaryMain}
        durationInFrames={scriptData.totalDurationInFrames || 36000}
        fps={scriptData.fps || 30}
        width={1440}
        height={1080}
      />
    </>
  );
};
