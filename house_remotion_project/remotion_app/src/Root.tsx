// C5-REAL EXERGY CERTIFIED
import { Composition } from "remotion";
import { HouseVisualizer } from "./HouseVisualizer";
import "./index.css";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="HouseVisualizer"
        component={HouseVisualizer}
        durationInFrames={1800}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
