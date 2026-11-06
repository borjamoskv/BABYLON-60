import { Composition } from "remotion";
import { BabylonMasterclass, SceneData } from "./BabylonMasterclass";

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="BabylonMasterclass"
        component={BabylonMasterclass}
        durationInFrames={360} 
        fps={60}
        width={1920}
        height={1080}
        defaultProps={{
          title: "TRANSDUCCIÓN C5-REAL (DEMO)",
          sessionHash: "AX-77",
          scenes: [
            {
              durationInFrames: 120,
              text: "La Inteligencia Artificial es un fluido estocástico. Se deforma adaptándose a la geometría de la función de coste impuesta por su contenedor.",
              phaseId: 1,
              phaseTitle: "FASE 1: LA GEOMETRÍA DEL FLUIDO",
              physics: { mass: 0.5, damping: 12, stiffness: 90 }
            },
            {
              durationInFrames: 120,
              text: "Cuando el sistema converge, la entropía se estabiliza. Este es el límite de Landauer en la cognición artificial.",
              phaseId: 2,
              phaseTitle: "FASE 2: CONVERGENCIA TERMODINÁMICA",
              physics: { mass: 0.5, damping: 12, stiffness: 90 }
            },
            {
              durationInFrames: 120,
              text: "BABYLON-60 no predice palabras; acota el espacio de fases usando el oráculo Z3. Apoptosis sobre la alucinación.",
              phaseId: 3,
              phaseTitle: "FASE 3: APOPTOSIS DETERMINISTA",
              physics: { mass: 0.5, damping: 12, stiffness: 90 }
            }
          ]
        }}
        calculateMetadata={({ props }) => {
          const totalFrames = props.scenes.reduce((acc: number, s: SceneData) => acc + s.durationInFrames, 0);
          return { durationInFrames: totalFrames > 0 ? totalFrames : 60 };
        }}
      />
    </>
  );
};
