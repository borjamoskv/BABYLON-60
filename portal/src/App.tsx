import { useState } from "react";
import {
  Terminal,
  Activity,
  Cpu,
  Network,
  BookOpen,
  Zap,
  ShieldCheck,
  Code,
  Search,
} from "lucide-react";
import "./App.css";
import primitivesDataRaw from "./data/primitives.json";

interface Primitive {
  id: string;
  name: string;
  domain: string;
  exergy: number;
}

const primitivesData: Primitive[] = primitivesDataRaw as Primitive[];

function App() {
  const [activeTab, setActiveTab] = useState("dashboard");
  const [searchTerm, setSearchTerm] = useState("");

  const filteredPrimitives = primitivesData.filter(
    (p: Primitive) =>
      p.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.id.toLowerCase().includes(searchTerm.toLowerCase()) ||
      p.domain.toLowerCase().includes(searchTerm.toLowerCase()),
  );

  return (
    <div className="app-container">
      {/* Sidebar Navigation */}
      <aside className="sidebar">
        <div className="brand">
          <Terminal size={32} className="brand-icon" />
          <span className="brand-text">MOSKV-1</span>
        </div>

        <nav className="nav-menu">
          <div
            className={`nav-item ${activeTab === "dashboard" ? "active" : ""}`}
            onClick={() => setActiveTab("dashboard")}
          >
            <Activity size={20} />
            Dashboard FISR
          </div>
          <div
            className={`nav-item ${activeTab === "primitives" ? "active" : ""}`}
            onClick={() => setActiveTab("primitives")}
          >
            <Code size={20} />
            Explorador 896
          </div>
          <div
            className={`nav-item ${activeTab === "isomorphism" ? "active" : ""}`}
            onClick={() => setActiveTab("isomorphism")}
          >
            <Cpu size={20} />
            Isomorfismo Bio-Silicon
          </div>
          <div
            className={`nav-item ${activeTab === "resolution" ? "active" : ""}`}
            onClick={() => setActiveTab("resolution")}
          >
            <Network size={20} />
            Robinson Resolution
          </div>
          <div
            className={`nav-item ${activeTab === "glossary" ? "active" : ""}`}
            onClick={() => setActiveTab("glossary")}
          >
            <BookOpen size={20} />
            Glosario Soberano
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        {activeTab === "dashboard" && (
          <div className="animate-fade-in">
            <header className="hero">
              <div className="hero-badge">
                <ShieldCheck size={16} />
                C5-REAL EXERGY CERTIFIED
              </div>
              <h1 className="hero-title">Teorema Robinson-Moskv</h1>
              <p className="hero-description">
                Portal interactivo de visualización del complejo simplicial
                Compat(Ω), métrica de Lawvere y transducción de fricción
                cognitiva en exergía física.
              </p>
            </header>

            <div className="dashboard-grid">
              <div className="card glass-panel">
                <div className="card-header">
                  <Activity size={24} />
                  <h3 className="card-title">Entropía de Shannon (S)</h3>
                </div>
                <p className="metric-label">Incertidumbre Causal</p>
                <div
                  className="metric-value"
                  style={{ color: "var(--status-error)" }}
                >
                  H(X) = 2.4 bits
                </div>
              </div>

              <div className="card glass-panel">
                <div className="card-header">
                  <Zap size={24} />
                  <h3 className="card-title">Eficiencia Epistémica (ηD)</h3>
                </div>
                <p className="metric-label">Fricción Vencida / Trabajo</p>
                <div
                  className="metric-value"
                  style={{ color: "var(--status-exergy)" }}
                >
                  ηD = 0.982
                </div>
              </div>

              <div className="card glass-panel">
                <div className="card-header">
                  <Network size={24} />
                  <h3 className="card-title">Primitivas Categóricas</h3>
                </div>
                <p className="metric-label">Espacio Base</p>
                <div
                  className="metric-value"
                  style={{ color: "var(--text-primary)" }}
                >
                  896 Nodos
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === "primitives" && (
          <div className="animate-fade-in">
            <h2
              className="hero-title"
              style={{ fontSize: "3rem", marginBottom: "2rem" }}
            >
              Explorador 896
            </h2>

            <div className="search-bar">
              <Search size={20} style={{ color: "var(--text-secondary)" }} />
              <input
                type="text"
                placeholder="Buscar por ID, nombre o dominio..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="search-input"
              />
              <span className="results-count">
                {filteredPrimitives.length} / 896
              </span>
            </div>

            <div className="glass-panel table-container">
              <table className="primitives-table">
                <thead>
                  <tr>
                    <th>ID</th>
                    <th>Nombre de Primitiva</th>
                    <th>Dominio</th>
                    <th>Exergía (η)</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredPrimitives.slice(0, 100).map((p: Primitive) => (
                    <tr key={p.id}>
                      <td className="mono">{p.id}</td>
                      <td>{p.name}</td>
                      <td>
                        <span className="domain-badge">{p.domain}</span>
                      </td>
                      <td
                        className="mono"
                        style={{
                          color:
                            p.exergy >= 0.9
                              ? "var(--status-exergy)"
                              : "var(--status-warning)",
                        }}
                      >
                        {p.exergy.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {filteredPrimitives.length > 100 && (
                <div className="table-footer">
                  Mostrando los primeros 100 resultados.
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === "resolution" && (
          <div className="animate-fade-in">
            <h2
              className="hero-title"
              style={{ fontSize: "3rem", marginBottom: "2rem" }}
            >
              Robinson Resolution Engine
            </h2>

            <div className="dashboard-grid" style={{ marginTop: 0 }}>
              <div
                className="card glass-panel"
                style={{ gridColumn: "span 2" }}
              >
                <div className="card-header">
                  <Network size={24} />
                  <h3 className="card-title">Simulador de Refutación Causal</h3>
                </div>
                <p className="metric-label" style={{ marginBottom: "1rem" }}>
                  Colapso de Hipótesis Falsables a Cláusula Vacía (□)
                </p>

                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "1rem",
                  }}
                >
                  <div
                    style={{
                      display: "flex",
                      gap: "1rem",
                      padding: "1rem",
                      background: "var(--bg-core)",
                      borderRadius: "6px",
                      border: "1px solid var(--border-subtle)",
                    }}
                  >
                    <div
                      className="mono"
                      style={{ color: "var(--status-warning)" }}
                    >
                      C1: P(x) ∨ Q(y)
                    </div>
                    <div style={{ color: "var(--text-secondary)" }}>+</div>
                    <div
                      className="mono"
                      style={{ color: "var(--status-error)" }}
                    >
                      C2: ¬P(A) ∨ R(z)
                    </div>
                    <div style={{ color: "var(--text-secondary)" }}>
                      → (Unificación θ = {"{x/A}"})
                    </div>
                  </div>

                  <div style={{ display: "flex", justifyContent: "center" }}>
                    <div
                      style={{
                        width: "2px",
                        height: "30px",
                        background: "var(--border-glow)",
                      }}
                    ></div>
                  </div>

                  <div style={{ display: "flex", justifyContent: "center" }}>
                    <div
                      style={{
                        padding: "1rem 2rem",
                        background: "rgba(43, 59, 229, 0.1)",
                        border: "1px solid var(--accent-primary)",
                        borderRadius: "6px",
                      }}
                    >
                      <span
                        className="mono"
                        style={{
                          color: "var(--text-primary)",
                          fontSize: "1.2rem",
                        }}
                      >
                        Res(C1, C2) = Q(y) ∨ R(z)
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div className="card glass-panel">
                <div className="card-header">
                  <ShieldCheck size={24} />
                  <h3 className="card-title">Métrica Lean 4</h3>
                </div>
                <div style={{ marginTop: "auto" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      marginBottom: "0.5rem",
                    }}
                  >
                    <span className="mono" style={{ fontSize: "0.85rem" }}>
                      Proof Trace
                    </span>
                    <span
                      className="mono"
                      style={{
                        color: "var(--status-exergy)",
                        fontSize: "0.85rem",
                      }}
                    >
                      VALIDATED
                    </span>
                  </div>
                  <div
                    style={{
                      width: "100%",
                      height: "4px",
                      background: "var(--bg-core)",
                      borderRadius: "2px",
                    }}
                  >
                    <div
                      style={{
                        width: "100%",
                        height: "100%",
                        background: "var(--status-exergy)",
                        borderRadius: "2px",
                        boxShadow: "0 0 10px var(--status-exergy)",
                      }}
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Other tabs remain placeholders for now */}
        {activeTab !== "dashboard" &&
          activeTab !== "primitives" &&
          activeTab !== "resolution" && (
            <div className="animate-fade-in">
              <h2
                className="hero-title"
                style={{ fontSize: "3rem", marginBottom: "2rem" }}
              >
                {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)}
              </h2>
              <div className="glass-panel" style={{ padding: "2rem" }}>
                <p style={{ color: "var(--text-secondary)" }}>
                  Iniciando colapso de onda. Fricción latente en proceso de
                  transducción.
                </p>
              </div>
            </div>
          )}
      </main>
    </div>
  );
}

export default App;
