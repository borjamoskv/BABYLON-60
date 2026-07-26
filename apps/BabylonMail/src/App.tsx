import React, { useState, useEffect } from "react";
import { Mail, Send, Inbox, ShieldCheck, FileText, CheckCircle2, RefreshCw } from "lucide-react";

interface Email {
  id: string;
  from: string;
  to: string;
  subject: string;
  body: string;
  date: string;
  unread: boolean;
}

export default function App() {
  const [activeTab, setActiveTab] = useState<"inbox" | "sent" | "drafts">("inbox");
  const [accountEmail, setAccountEmail] = useState<string>("borja@babylon60.com");
  const [isProvisioned, setIsProvisioned] = useState<boolean>(true);
  const [selectedMail, setSelectedMail] = useState<Email | null>(null);

  const [emails, setEmails] = useState<Email[]>([
    {
      id: "msg_001",
      from: "hypervisor@babylon60.com",
      to: "borja@babylon60.com",
      subject: "⚡ BFT Attestation: Enjambre 100 ULTRATHINK Operativo",
      body: "Estimado Operador,\n\nLa instalación de BabylonMail ha aprovisionado automáticamente tu cuenta soberana @babylon60.com. El enjambre de 100 agentes ULTRATHINK ha completado la validación BFT y el ledger BFT se encuentra sellado (Commit 664a9f3b5f).\n\nInvariantes C5-REAL: 1000.0/1000.0 Exergía.\n\nAtentamente,\nCORTEX Hypervisor",
      date: "21:32:00",
      unread: true,
    },
    {
      id: "msg_002",
      from: "security@babylon60.com",
      to: "borja@babylon60.com",
      subject: "🛡️ Claves Criptográficas Ed25519 Aprovisionadas",
      body: "Se han generado y vinculado automáticamente las claves criptográficas Ed25519 para tu usuario borja@babylon60.com durante la instalación local en macOS Tahoe 26.5.2.\n\nHash Taint: 7536b90af4baa146ac60d719982be602081bd18d",
      date: "21:30:15",
      unread: false,
    },
  ]);

  const [composeOpen, setComposeOpen] = useState(false);
  const [composeTo, setComposeTo] = useState("");
  const [composeSubject, setComposeSubject] = useState("");
  const [composeBody, setComposeBody] = useState("");

  useEffect(() => {
    // Simulación de auto-aprovisionamiento de cuenta en primera instalación
    const savedUser = localStorage.getItem("babylon_mail_user");
    if (!savedUser) {
      localStorage.setItem("babylon_mail_user", "borja@babylon60.com");
    }
    if (emails.length > 0) {
      setSelectedMail(emails[0]);
    }
  }, []);

  const handleSendEmail = (e: React.FormEvent) => {
    e.preventDefault();
    if (!composeTo || !composeSubject) return;

    const newEmail: Email = {
      id: `msg_${Date.now()}`,
      from: accountEmail,
      to: composeTo,
      subject: composeSubject,
      body: composeBody,
      date: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      unread: false,
    };

    setEmails([newEmail, ...emails]);
    setComposeOpen(false);
    setComposeTo("");
    setComposeSubject("");
    setComposeBody("");
    setSelectedMail(newEmail);
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <div className="sidebar">
        <div className="brand">
          <div className="brand-icon">
            <Mail size={20} color="#fff" />
          </div>
          <span className="brand-title">BabylonMail</span>
        </div>

        {/* User Account Auto-Provisioned Badge */}
        <div className="user-badge">
          <div className="user-label">Cuenta Aprovisionada</div>
          <div className="user-email">{accountEmail}</div>
          {isProvisioned && (
            <div className="auto-provisioned-banner">
              <CheckCircle2 size={14} />
              <span>Instalación Automática</span>
            </div>
          )}
        </div>

        <ul className="nav-menu">
          <li
            className={`nav-item ${activeTab === "inbox" ? "active" : ""}`}
            onClick={() => setActiveTab("inbox")}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Inbox size={18} />
              <span>Entrada</span>
            </div>
            <span className="badge">{emails.length}</span>
          </li>
          <li
            className={`nav-item ${activeTab === "sent" ? "active" : ""}`}
            onClick={() => setActiveTab("sent")}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <Send size={18} />
              <span>Enviados</span>
            </div>
          </li>
          <li
            className={`nav-item ${activeTab === "drafts" ? "active" : ""}`}
            onClick={() => setActiveTab("drafts")}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
              <FileText size={18} />
              <span>Borradores</span>
            </div>
          </li>
        </ul>

        {/* Merkle Root SHA3-256 Attestation Card */}
        <div className="merkle-card">
          <div className="merkle-label">
            <ShieldCheck size={14} color="#10b981" />
            <span>Merkle Root SHA3-256</span>
          </div>
          <div className="merkle-root-hash">a0e0c70bc69873c4...</div>
          <div style={{ color: "#10b981", fontSize: "0.68rem", marginTop: "4px", fontWeight: 600 }}>
            🟢 BFT Ledger Inmutable
          </div>
        </div>
      </div>

      {/* Mail List */}
      <div className="mail-list-container">
        <div className="list-header">
          <span className="list-title">Bandeja de Entrada</span>
          <button className="compose-btn" onClick={() => setComposeOpen(true)}>
            + Redactar
          </button>
        </div>

        <div className="mail-items">
          {emails.map((mail) => (
            <div
              key={mail.id}
              className={`mail-card ${selectedMail?.id === mail.id ? "selected" : ""}`}
              onClick={() => setSelectedMail(mail)}
            >
              <div className="mail-card-header">
                <span className="sender-name">{mail.from.split("@")[0]}</span>
                <span className="mail-time">{mail.date}</span>
              </div>
              <div className="mail-subject">{mail.subject}</div>
              <div className="mail-preview">{mail.body}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Mail Detail View / Compose Modal */}
      <div className="mail-detail">
        {composeOpen ? (
          <div style={{ padding: "32px", display: "flex", flexDirection: "column", height: "100%" }}>
            <h2 style={{ marginBottom: "20px" }}>Nuevo Mensaje (@babylon60.com)</h2>
            <form onSubmit={handleSendEmail} style={{ display: "flex", flexDirection: "column", gap: "16px", flex: 1 }}>
              <input
                type="email"
                placeholder="Para: destinatario@babylon60.com"
                value={composeTo}
                onChange={(e) => setComposeTo(e.target.value)}
                style={{
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-color)",
                  color: "#fff",
                  padding: "12px",
                  borderRadius: "6px",
                }}
                required
              />
              <input
                type="text"
                placeholder="Asunto"
                value={composeSubject}
                onChange={(e) => setComposeSubject(e.target.value)}
                style={{
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-color)",
                  color: "#fff",
                  padding: "12px",
                  borderRadius: "6px",
                }}
                required
              />
              <textarea
                placeholder="Escribe tu correo..."
                value={composeBody}
                onChange={(e) => setComposeBody(e.target.value)}
                style={{
                  background: "var(--bg-tertiary)",
                  border: "1px solid var(--border-color)",
                  color: "#fff",
                  padding: "12px",
                  borderRadius: "6px",
                  flex: 1,
                  resize: "none",
                }}
                required
              />
              <div style={{ display: "flex", gap: "12px", justifyContent: "flex-end" }}>
                <button
                  type="button"
                  onClick={() => setComposeOpen(false)}
                  style={{
                    background: "transparent",
                    color: "var(--text-muted)",
                    border: "1px solid var(--border-color)",
                    padding: "10px 20px",
                    borderRadius: "6px",
                    cursor: "pointer",
                  }}
                >
                  Cancelar
                </button>
                <button type="submit" className="compose-btn">
                  Enviar Correo
                </button>
              </div>
            </form>
          </div>
        ) : selectedMail ? (
          <>
            <div className="detail-header">
              <div className="detail-subject">{selectedMail.subject}</div>
              <div className="detail-meta">
                <div className="avatar">{selectedMail.from[0].toUpperCase()}</div>
                <div className="meta-info">
                  <span className="from-email">{selectedMail.from}</span>
                  <span className="to-email">Para: {selectedMail.to}</span>
                </div>
              </div>
            </div>
            <div className="detail-body">
              <pre style={{ fontFamily: "inherit", whiteSpace: "pre-wrap" }}>{selectedMail.body}</pre>
            </div>
          </>
        ) : (
          <div style={{ padding: "32px", color: "var(--text-muted)" }}>Selecciona un correo para leer.</div>
        )}
      </div>
    </div>
  );
}
