// C5-REAL EXERGY CERTIFIED
import React from "react";
import { useCurrentFrame, interpolate, spring, useVideoConfig } from "remotion";

export interface DataVizSceneProps {
  broll: string;
}

export const DataVizScene: React.FC<DataVizSceneProps> = ({ broll }) => {
  const frame = useCurrentFrame();
  const { fps, width, height } = useVideoConfig();

  // Animaciones de fondo reactivas por tiempo
  const pulse = Math.sin(frame / 15) * 10;
  const rotation = (frame / 2) % 360;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        backgroundColor: "#020617",
        display: "flex",
        justifyContent: "center",
        alignItems: "center",
        overflow: "hidden"
      }}
    >
      {/* Fondo de rejilla Cyberpunk / Retro-Investigación */}
      <div
        style={{
          position: "absolute",
          inset: -100,
          backgroundImage:
            "radial-gradient(circle, rgba(56, 189, 248, 0.15) 1px, transparent 1px)",
          backgroundSize: "40px 40px",
          transform: `translateY(${(frame * 2) % 40}px)`
        }}
      />

      {/* Renderizado dinámico según la escena B-Roll */}
      {broll === "token_chart" && (
        <div
          style={{
            width: "800px",
            height: "450px",
            backgroundColor: "rgba(15, 23, 42, 0.9)",
            backdropFilter: "blur(20px)",
            borderRadius: "24px",
            border: "1px solid rgba(239, 68, 68, 0.4)",
            padding: "36px",
            display: "flex",
            flexDirection: "column",
            gap: "20px",
            boxShadow: "0 25px 60px rgba(239, 68, 68, 0.2)"
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <h2 style={{ color: "#ef4444", fontSize: "28px", margin: 0, fontFamily: "monospace" }}>
              SERIE ARITMÉTICA DE TOKEN BURN (360 ITERACIONES)
            </h2>
            <span style={{ color: "#f8fafc", fontWeight: 800, fontSize: "24px" }}>
              Total: $61.56 USD
            </span>
          </div>

          <div
            style={{
              flex: 1,
              display: "flex",
              alignItems: "flex-end",
              gap: "8px",
              paddingTop: "40px",
              borderBottom: "2px solid #475569"
            }}
          >
            {Array.from({ length: 30 }).map((_, i) => {
              const heightPct = interpolate(i, [0, 29], [15, 100]);
              const animatedHeight = spring({
                frame: frame - i * 2,
                fps,
                config: { damping: 12 }
              });

              return (
                <div
                  key={i}
                  style={{
                    flex: 1,
                    height: `${Math.max(5, heightPct * Math.min(1, Math.max(0, animatedHeight)))}%`,
                    backgroundColor: i > 22 ? "#ef4444" : i > 12 ? "#f59e0b" : "#3b82f6",
                    borderRadius: "4px 4px 0 0"
                  }}
                />
              );
            })}
          </div>

          <p style={{ color: "#94a3b8", fontSize: "16px", fontFamily: "sans-serif" }}>
            Acumulación lineal de la Ventana de Contexto (4,000 → 100,000 tokens per call).
          </p>
        </div>
      )}

      {broll === "mcp_diagram" && (
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "40px",
            padding: "40px",
            backgroundColor: "rgba(15, 23, 42, 0.85)",
            borderRadius: "24px",
            border: "1px solid rgba(56, 189, 248, 0.3)"
          }}
        >
          <div
            style={{
              padding: "24px 36px",
              backgroundColor: "#1e1b4b",
              borderRadius: "16px",
              color: "#818cf8",
              fontSize: "24px",
              fontWeight: 800,
              border: "2px solid #6366f1"
            }}
          >
            LLM CLIENT (Claude)
          </div>
          <div style={{ color: "#38bdf8", fontSize: "32px", fontWeight: 900 }}>
            ◄─── MCP PROTOCOL ───►
          </div>
          <div
            style={{
              padding: "24px 36px",
              backgroundColor: "#064e3b",
              borderRadius: "16px",
              color: "#34d399",
              fontSize: "24px",
              fontWeight: 800,
              border: "2px solid #10b981"
            }}
          >
            MCP SERVER (Tools & APIs)
          </div>
        </div>
      )}

      {/* Fondo por defecto para otras escenas (Efecto Holo-Orb) */}
      {broll !== "token_chart" && broll !== "mcp_diagram" && (
        <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "24px" }}>
          <div
            style={{
              width: `${300 + pulse * 4}px`,
              height: `${300 + pulse * 4}px`,
              borderRadius: "50%",
              background: "radial-gradient(circle, rgba(139, 92, 246, 0.6) 0%, rgba(15, 23, 42, 0) 70%)",
              border: "2px dashed #8b5cf6",
              transform: `rotate(${rotation}deg)`,
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              boxShadow: "0 0 80px rgba(139, 92, 246, 0.4)"
            }}
          >
            <span
              style={{
                fontSize: "28px",
                fontWeight: 900,
                color: "#ffffff",
                fontFamily: "monospace",
                textTransform: "uppercase",
                transform: `rotate(-${rotation}deg)`
              }}
            >
              [{broll}]
            </span>
          </div>
        </div>
      )}
    </div>
  );
};
