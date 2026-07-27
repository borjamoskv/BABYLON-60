// C5-REAL EXERGY CERTIFIED
import React, { useState, useEffect } from "react";

/**
 * C5-REAL: IDE Layout
 * Topología tripartita que colapsa el código, el navegador y el agente
 * en un solo espacio termodinámico.
 */

export const IdeLayout: React.FC = () => {
  const [isBrowserOpen, setIsBrowserOpen] = useState(false);

  // Escuchar atajos globales (ej: Cmd+B) para mostrar el Browser Pane
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.metaKey && e.key === "b") {
        setIsBrowserOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div
      style={{
        display: "flex",
        height: "100vh",
        width: "100vw",
        backgroundColor: "var(--surface, #0F1226)",
      }}
    >
      {/* 1. Árbol de archivos / Sidebar del Editor (15%) */}
      <div
        style={{
          width: "15%",
          borderRight: "1px solid var(--border, #2E3866)",
        }}
      >
        <h3 style={{ color: "var(--text, #FFF)", padding: "1rem" }}>
          Workspace
        </h3>
        {/* Aquí iría el File Tree */}
      </div>

      {/* 2. Editor de Código (Flex) */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column" }}>
        <div style={{ flex: 1, padding: "1rem", color: "var(--text, #FFF)" }}>
          {/* Aquí iría el Monaco Editor o similar */}
          <h3>Editor Pane (C5-REAL Code)</h3>
          <p>Press Cmd+B to toggle Browser Pane.</p>
        </div>
      </div>

      {/* 3. Browser Pane Transparente (30% si está abierto) */}
      {isBrowserOpen && (
        <div
          id="browser-pane-container"
          style={{
            width: "30%",
            borderLeft: "1px solid var(--border, #2E3866)",
            position: "relative",
          }}
        >
          {/*
            Este contenedor es un "agujero" en React.
            El Main Process de Electron proyectará el WebContentsView nativo exactamente sobre estas coordenadas
            midiendo el boundingClientRect de este div.
          */}
        </div>
      )}

      {/* 4. Agent Igor Sidebar (20%) */}
      <div
        style={{
          width: "20%",
          borderLeft: "1px solid var(--border, #2E3866)",
          backgroundColor: "var(--bg, #090B19)",
        }}
      >
        <h3 style={{ color: "var(--lapis, #3B4DFF)", padding: "1rem" }}>
          MOSKV-1 APEX: AGENT IGOR
        </h3>
        <div style={{ padding: "1rem", color: "var(--muted, #B4B9DF)" }}>
          Agent Context: {isBrowserOpen ? "Dual (Code + DOM)" : "Single (Code)"}
        </div>
        {/* Aquí iría la interfaz de chat del agente */}
      </div>
    </div>
  );
};
