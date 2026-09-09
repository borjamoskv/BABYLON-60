import { Composition } from "remotion";
import { BabylonMasterclass, SceneData } from "./BabylonMasterclass";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BabylonMasterclass"
        component={BabylonMasterclass}
        durationInFrames={900} 
        fps={60}
        width={1920}
        height={1080}
        defaultProps={{
          title: "CARGANDO ORÁCULO...",
          sessionHash: "AX-STANDBY",
          scenes: []
        }}
        calculateMetadata={({ props }) => {
          const totalFrames = props.scenes.reduce((acc: number, s: SceneData) => acc + s.durationInFrames, 0);
          return { durationInFrames: totalFrames > 0 ? totalFrames : 60 };
        }}
      />
    </>
  );
};
