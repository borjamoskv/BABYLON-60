// C5-REAL EXERGY CERTIFIED
import React from "react";
import { Sequence, Audio } from "remotion";
import scriptData from "./script.json";
import { SpeakerCard } from "./components/SpeakerCard";
import { ChapterTitleScene } from "./components/ChapterTitleScene";
import { WordLevelSubtitles } from "./components/WordLevelSubtitles";
import { DataVizScene } from "./components/DataVizScene";

export const DocumentaryMain: React.FC = () => {
  return (
    <div
      style={{
        position: "relative",
        width: "100%",
        height: "100%",
        backgroundColor: "#020617",
        overflow: "hidden"
      }}
    >
      {scriptData.lines.map((line) => {
        const chapter = scriptData.chapters.find((c) => c.id === line.chapterId);

        return (
          <Sequence
            key={line.id}
            from={line.startFrame}
            durationInFrames={line.durationInFrames}
          >
            {/* 1. Fondo reactivo / B-Roll */}
            <DataVizScene broll={line.broll} />

            {/* 2. Pista de Audio Nativa (<Audio> Remotion) */}
            <Audio src={line.audioFile} />

            {/* 3. Tarjeta de personaje hablante */}
            <SpeakerCard
              speaker={line.speaker}
              voice={line.voice}
              color={line.avatarColor}
            />

            {/* 4. Banner de título de capítulo */}
            {chapter && (
              <ChapterTitleScene
                chapterTitle={chapter.title}
                subtitle={chapter.subtitle}
              />
            )}

            {/* 5. Subtítulos dinámicos a nivel de palabra */}
            <WordLevelSubtitles
              timestamps={line.wordTimestamps}
              activeColor={line.avatarColor}
            />
          </Sequence>
        );
      })}
    </div>
  );
};
