// C5-REAL EXERGY CERTIFIED
import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";
import App from "./App.tsx";
import { startExergyStream } from "./api/bridge";

// Ignite the gRPC-Web Exergy Stream Bridge
startExergyStream();

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
