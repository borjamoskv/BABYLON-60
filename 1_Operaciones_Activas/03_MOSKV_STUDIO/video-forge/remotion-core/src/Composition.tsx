// C5-REAL EXERGY CERTIFIED
import { Composition } from "remotion";
import { CortexVideo } from "./CortexVideo";
import script from "./script.json";

export const MyComposition = () => {
  const totalDuration = script.reduce((acc, scene) => acc + scene.durationFrames, 0);

  return (
    <Composition
      id="CortexImperial"
      component={CortexVideo}
      durationInFrames={totalDuration || 300}
      fps={30}
      width={1440} // 4:3 Aspect Ratio
      height={1080}
    />
  );
};
