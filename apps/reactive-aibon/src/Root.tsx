import "./index.css";
import { ALL_FORMATS, Input, UrlSource } from "mediabunny";
import { Composition, staticFile } from "remotion";
import { AibonScene } from "./Visualizer/AibonScene";
import { visualizerCompositionSchema } from "./helpers/schema";

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="AibonReactive"
        component={AibonScene}
        width={1440}
        height={1080}
        schema={visualizerCompositionSchema}
        defaultProps={{
          // audio settings
          audioOffsetInSeconds: 0,
          audioSrc: staticFile("audio.mp3"),
        }}
        // Determine the length of the video based on the duration of the audio file
        calculateMetadata={async ({ props }) => {
          const input = new Input({
            source: new UrlSource(props.audioSrc, {
              getRetryDelay: () => null,
            }),
            formats: ALL_FORMATS,
          });

          const durationInSeconds = await input.computeDuration();

          return {
            durationInFrames: Math.floor(
              (durationInSeconds - props.audioOffsetInSeconds) * FPS,
            ),
            fps: FPS,
          };
        }}
      />
    </>
  );
};
