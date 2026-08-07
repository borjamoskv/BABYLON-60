// C5-REAL EXERGY CERTIFIED
import "./index.css";
import { IntervaloProhibidoSequelRoot } from "./Composition";
import { GonFictionComposition, GON_FICTION_DURATION_FRAMES } from "./GonFictionComposition";
import { Composition } from "remotion";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <IntervaloProhibidoSequelRoot />
      <Composition
        id="GonFiction8Bit"
        component={GonFictionComposition}
        durationInFrames={GON_FICTION_DURATION_FRAMES}
        fps={30}
        width={1080}
        height={1920}
      />
    </>
  );
};
