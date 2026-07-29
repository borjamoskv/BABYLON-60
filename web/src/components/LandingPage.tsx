import { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowRight, Zap, Check, Shield, Database, Search, Clock, Lock, Code, Globe, Server } from 'lucide-react';
import './LandingPage.css';

interface LandingPageProps {
  onEnter: () => void;
}

/* ── Live telemetry feed ── */
const TELEMETRY = [
  { text: 'memory.store(type="decision", content="Selected vendor B...")', type: 'info' },
  { text: '✓ SHA256 chain extended · hash: 0x7f3a...d91c', type: 'success' },
  { text: 'memory.search("vendor selection criteria", top_k=5)', type: 'info' },
  { text: '✓ 5 results · hybrid score: 0.94 · latency: 2.1ms', type: 'success' },
  { text: 'memory.store(type="error", content="API timeout on retry 3")', type: 'info' },
  { text: '✓ Lineage attached · parent: 0x4a2e...8bf1 · depth: 7', type: 'success' },
  { text: '⚠ Collision detected on mutation_hash · payload differs', type: 'warn' },
  { text: '✗ INV_BFT_04: Tamper attempt blocked. Transaction aborted.', type: 'error' },
  { text: '✓ Integrity verified · ledger consistent · 847 entries', type: 'success' },
  { text: 'audit.export(format="json", range="last_7d")', type: 'info' },
  { text: '✓ Audit report generated · 2,341 operations · 0 anomalies', type: 'success' },
];

export function LandingPage({ onEnter }: LandingPageProps) {
  const [visibleLines, setVisibleLines] = useState<typeof TELEMETRY>([]);
  const [heroVisible, setHeroVisible] = useState(false);
  const [activeTab, setActiveTab] = useState<'python' | 'cli'>('python');
  const observerRefs = useRef<(HTMLElement | null)[]>([]);
  const [revealedSections, setRevealedSections] = useState<Set<number>>(new Set());

  useEffect(() => {
    const t = setTimeout(() => setHeroVisible(true), 100);
    return () => clearTimeout(t);
  }, []);

  useEffect(() => {
    let idx = 0;
    const interval = setInterval(() => {
      setVisibleLines(prev => {
        const next = [...prev, TELEMETRY[idx % TELEMETRY.length]];
        return next.length > 7 ? next.slice(-7) : next;
      });
      idx++;
    }, 2200);
    return () => clearInterval(interval);
  }, []);

  const setRef = useCallback((el: HTMLElement | null, index: number) => {
    observerRefs.current[index] = el;
  }, []);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach(entry => {
          if (entry.isIntersecting) {
            const idx = Number(entry.target.getAttribute('data-reveal-idx'));
            setRevealedSections(prev => new Set(prev).add(idx));
          }
        });
      },
      { threshold: 0.12 }
    );
    observerRefs.current.forEach(el => { if (el) observer.observe(el); });
    return () => observer.disconnect();
  }, []);

  const revealClass = (idx: number) =>
    `reveal-section ${revealedSections.has(idx) ? 'revealed' : ''}`;

  return (
    <div className="landing-container">
      {/* ── Particles ── */}
      <div className="particle-field" aria-hidden="true">
        {Array.from({ length: 30 }).map((_, i) => (
          <div key={i} className="particle" style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
            animationDelay: `${Math.random() * 8}s`,
            animationDuration: `${6 + Math.random() * 10}s`,
          }} />
        ))}
      </div>

      {/* ── Nav ── */}
      <nav className="landing-nav">
        <div className="landing-brand">
          <Zap className="landing-logo" />
          <span>BABYLON-60</span>
        </div>
        <div className="nav-right">
          <a href="#features" className="nav-link-ghost">Features</a>
          <a href="#pricing" className="nav-link-ghost">Pricing</a>
          <a href="https://github.com/borjamoskv/BABYLON-60/tree/main/docs" className="nav-link-ghost" target="_blank" rel="noopener noreferrer">Docs</a>
          <a href="https://github.com/borjamoskv/BABYLON-60" className="nav-link-ghost" target="_blank" rel="noopener noreferrer">GitHub</a>
          <button className="landing-cta-outline" onClick={onEnter}>Dashboard</button>
        </div>
      </nav>

      {/* ══════════════════ HERO ══════════════════ */}
      <section className={`landing-hero ${heroVisible ? 'hero-entered' : ''}`}>
        <div className="hero-content">
          <div className="hero-badge">
            <span className="badge-dot" />
            NOW IN PUBLIC BETA
          </div>

          <h1 className="hero-title">
            Tamper-proof memory<br />
            <span className="hero-accent">for AI agents</span>
          </h1>

          <p className="hero-subtitle">
            Your agent makes thousands of decisions. Can you prove a single one wasn't tampered with?
            BABYLON-60 gives your AI stack persistent, verifiable, and searchable memory — with cryptographic audit trails built in.
          </p>

          <div className="hero-actions">
            <button className="landing-cta-primary" onClick={onEnter}>
              Get Started Free <ArrowRight className="cta-icon" />
            </button>
            <a href="https://github.com/borjamoskv/BABYLON-60" target="_blank" rel="noopener noreferrer" className="landing-cta-secondary">
              View on GitHub →
            </a>
          </div>

          <div className="hero-install">
            <code>pip install babylon60</code>
          </div>
        </div>

        {/* Metrics strip */}
        <div className="metrics-strip">
          <div className="metric">
            <span className="metric-value">&lt;5ms</span>
            <span className="metric-label">Write latency</span>
          </div>
          <div className="metric-divider" />
          <div className="metric">
            <span className="metric-value">0</span>
            <span className="metric-label">Cloud dependencies</span>
          </div>
          <div className="metric-divider" />
          <div className="metric">
            <span className="metric-value">AES-256</span>
            <span className="metric-label">Encryption at rest</span>
          </div>
          <div className="metric-divider" />
          <div className="metric">
            <span className="metric-value">100%</span>
            <span className="metric-label">Open source core</span>
          </div>
        </div>
      </section>

      {/* ══════════════════ PROBLEM ══════════════════ */}
      <section
        className={revealClass(0)}
        ref={(el) => setRef(el, 0)}
        data-reveal-idx="0"
      >
        <div className="landing-problem">
          <div className="problem-grid">
            <div className="problem-text">
              <div className="section-eyebrow">THE PROBLEM</div>
              <h2>Your agents forget everything. Your logs prove nothing.</h2>
              <p className="problem-description">
                Vector databases retrieve text. They don't track <em>when</em> it changed, <em>how</em> it was derived, or <em>whether the history was tampered with</em>.
              </p>
              <ul className="problem-list">
                <li><span className="problem-x">✗</span> Context lost between sessions</li>
                <li><span className="problem-x">✗</span> No lineage on decisions</li>
                <li><span className="problem-x">✗</span> Audit trails are reconstruction theater</li>
                <li><span className="problem-x">✗</span> EU AI Act enforcement begins August 2026</li>
              </ul>
            </div>
            <div className="problem-visual">
              <div className="comparison-card bad">
                <div className="comparison-header">Without BABYLON-60</div>
                <div className="comparison-body">
                  <div className="comp-line faded">agent.remember("decision A")</div>
                  <div className="comp-line faded">// ...3 sessions later...</div>
                  <div className="comp-line faded">agent.recall("decision A")</div>
                  <div className="comp-line error">→ None  # Lost forever</div>
                </div>
              </div>
              <div className="comparison-card good">
                <div className="comparison-header">With BABYLON-60</div>
                <div className="comparison-body">
                  <div className="comp-line">memory.store(type="decision", ...)</div>
                  <div className="comp-line dim">// ...3 months later...</div>
                  <div className="comp-line">memory.search("decision A")</div>
                  <div className="comp-line success">→ Result(hash_chain=✓, lineage=7)</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ FEATURES ══════════════════ */}
      <section
        id="features"
        className={revealClass(1)}
        ref={(el) => setRef(el, 1)}
        data-reveal-idx="1"
      >
        <div className="landing-features">
          <div className="section-eyebrow center">WHAT YOU GET</div>
          <h2 className="features-title">Memory infrastructure that actually works.</h2>
          <div className="features-grid">
            <div className="feature-card-product">
              <Database className="feature-icon" />
              <h3>Structured Memory</h3>
              <p>Store facts, decisions, errors, and discoveries as typed units with metadata, confidence scores, and temporal validity.</p>
            </div>
            <div className="feature-card-product">
              <Lock className="feature-icon icon-amber" />
              <h3>Tamper-Evident Ledger</h3>
              <p>Every memory operation is hash-chained. If anything changes, the chain breaks. No silent overwrites. No data loss.</p>
            </div>
            <div className="feature-card-product">
              <Search className="feature-icon icon-green" />
              <h3>Hybrid Retrieval</h3>
              <p>Combine semantic and lexical search. Find context by meaning or by exact match — with latency under 5ms.</p>
            </div>
            <div className="feature-card-product">
              <Clock className="feature-icon icon-blue" />
              <h3>Memory Lifecycle</h3>
              <p>Promote, compact, decay, or archive memory. Your context window stays clean without losing anything permanently.</p>
            </div>
            <div className="feature-card-product">
              <Shield className="feature-icon icon-red" />
              <h3>Audit-Ready History</h3>
              <p>Export verifiable audit trails for compliance, postmortems, and regulatory review. EU AI Act ready out of the box.</p>
            </div>
            <div className="feature-card-product">
              <Server className="feature-icon icon-purple" />
              <h3>Local-First Runtime</h3>
              <p>SQLite + sqlite-vec by default. Zero cloud dependency. Runs on your laptop, your server, or your edge device.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ CODE EXAMPLE ══════════════════ */}
      <section
        className={revealClass(2)}
        ref={(el) => setRef(el, 2)}
        data-reveal-idx="2"
      >
        <div className="landing-code-section">
          <div className="code-layout">
            <div className="code-text">
              <div className="section-eyebrow">INTEGRATE IN MINUTES</div>
              <h2>Three lines to tamper-proof memory.</h2>
              <p>Install from PyPI. Initialize. Store your first verified memory. That's it.</p>
              <ul className="code-benefits">
                <li><Check size={16} className="check-green" /> Python-first API</li>
                <li><Check size={16} className="check-green" /> Async-friendly</li>
                <li><Check size={16} className="check-green" /> Type-safe with full IDE support</li>
                <li><Check size={16} className="check-green" /> Works with any LLM framework</li>
              </ul>
            </div>
            <div className="code-window">
              <div className="code-tabs">
                <button
                  className={`code-tab ${activeTab === 'python' ? 'active' : ''}`}
                  onClick={() => setActiveTab('python')}
                >
                  Python
                </button>
                <button
                  className={`code-tab ${activeTab === 'cli' ? 'active' : ''}`}
                  onClick={() => setActiveTab('cli')}
                >
                  CLI
                </button>
              </div>
              <div className="code-body">
                {activeTab === 'python' ? (
                  <pre><code>{`from babylon60 import Babylon60

# Initialize — local SQLite, zero config
b60 = Babylon60()

# Store a verified memory
b60.memory.store(
    content="Selected vendor B for cost efficiency",
    memory_type="decision",
    confidence=0.92,
    metadata={"project": "acme-migration"}
)

# Retrieve with hybrid search
results = b60.memory.search(
    query="vendor selection criteria",
    top_k=5
)

# Every result includes its hash chain
for r in results:
    print(r.content, r.hash_chain_valid)
    # → "Selected vendor B..." True`}</code></pre>
                ) : (
                  <pre><code>{`# Install
$ pip install babylon60

# Initialize a new memory store
$ b60 init --path ./my-agent-memory

# Store from CLI
$ b60 store \\
    --type decision \\
    --content "Selected vendor B" \\
    --confidence 0.92

# Search
$ b60 search "vendor selection"
┌─────────────────────────────────┐
│ 1. "Selected vendor B for..."   │
│    chain: ✓  confidence: 0.92   │
│    created: 2026-07-28T14:31Z   │
└─────────────────────────────────┘

# Export audit trail
$ b60 audit export --format json \\
    --range last_30d`}</code></pre>
                )}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ LIVE DEMO ══════════════════ */}
      <section
        className={revealClass(3)}
        ref={(el) => setRef(el, 3)}
        data-reveal-idx="3"
      >
        <div className="landing-telemetry">
          <div className="telemetry-header">
            <div className="section-eyebrow center">LIVE DEMO</div>
            <h2>Watch it work in real time.</h2>
            <p>Every store, search, and integrity check — hash-chained and verified.</p>
          </div>
          <div className="telemetry-window">
            <div className="terminal-chrome">
              <span className="chrome-dot red" />
              <span className="chrome-dot yellow" />
              <span className="chrome-dot green" />
              <span className="chrome-title">babylon60 · live telemetry</span>
            </div>
            <div className="telemetry-log">
              {visibleLines.length === 0 && (
                <div className="log-line blink"><code>Connecting to memory substrate...</code></div>
              )}
              {visibleLines.map((line, i) => (
                <div key={i} className={`log-line log-${line.type} ${i === visibleLines.length - 1 ? 'log-new' : ''}`}>
                  <code>{line.text}</code>
                </div>
              ))}
              <div className="cursor-line"><span className="terminal-cursor">█</span></div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ USE CASES ══════════════════ */}
      <section
        className={revealClass(4)}
        ref={(el) => setRef(el, 4)}
        data-reveal-idx="4"
      >
        <div className="landing-usecases">
          <div className="section-eyebrow center">USE CASES</div>
          <h2 className="features-title">Built for systems that can't afford amnesia.</h2>
          <div className="usecases-grid">
            <div className="usecase-card">
              <div className="usecase-icon">🤖</div>
              <h4>AI Agents with Tools</h4>
              <p>Persistent context across steps, sessions, and agent boundaries. No more "starting from scratch."</p>
            </div>
            <div className="usecase-card">
              <div className="usecase-icon">🔄</div>
              <h4>Long-Running Automation</h4>
              <p>Reduce drift, repetition, and memory loss in workflows that run for hours, days, or weeks.</p>
            </div>
            <div className="usecase-card">
              <div className="usecase-icon">⚖️</div>
              <h4>Compliance & Audit</h4>
              <p>Verifiable operational history for regulated environments. Export-ready for EU AI Act review.</p>
            </div>
            <div className="usecase-card">
              <div className="usecase-icon">🧠</div>
              <h4>Decision Systems</h4>
              <p>Track not just the output, but the full lineage of how a system arrived at each conclusion.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ PRICING ══════════════════ */}
      <section
        id="pricing"
        className={revealClass(5)}
        ref={(el) => setRef(el, 5)}
        data-reveal-idx="5"
      >
        <div className="landing-pricing">
          <div className="section-eyebrow center">PRICING</div>
          <h2 className="features-title">Start free. Scale when you need to.</h2>
          <div className="pricing-grid">
            <div className="pricing-card">
              <h3>Open Source</h3>
              <div className="price">$0<span>/forever</span></div>
              <p className="pricing-desc">For individuals and open-source projects.</p>
              <ul className="pricing-features">
                <li><Check size={14} /> Unlimited local memory stores</li>
                <li><Check size={14} /> Full hash-chain verification</li>
                <li><Check size={14} /> Hybrid search (semantic + lexical)</li>
                <li><Check size={14} /> SQLite + sqlite-vec runtime</li>
                <li><Check size={14} /> CLI and Python API</li>
                <li><Check size={14} /> MIT / Apache-2.0 license</li>
              </ul>
              <a href="https://github.com/borjamoskv/BABYLON-60" target="_blank" rel="noopener noreferrer" className="pricing-cta outline">
                Clone from GitHub
              </a>
            </div>
            <div className="pricing-card featured">
              <div className="pricing-badge">MOST POPULAR</div>
              <h3>Pro</h3>
              <div className="price">$49<span>/mo</span></div>
              <p className="pricing-desc">For teams shipping AI products.</p>
              <ul className="pricing-features">
                <li><Check size={14} /> Everything in Open Source</li>
                <li><Check size={14} /> Cloud sync & backup</li>
                <li><Check size={14} /> Team collaboration</li>
                <li><Check size={14} /> Audit export (JSON, CSV, PDF)</li>
                <li><Check size={14} /> Priority support</li>
                <li><Check size={14} /> EU AI Act compliance toolkit</li>
              </ul>
              <button className="pricing-cta primary" onClick={onEnter}>
                Start 14-Day Free Trial
              </button>
            </div>
            <div className="pricing-card">
              <h3>Enterprise</h3>
              <div className="price">Custom</div>
              <p className="pricing-desc">For regulated industries and large deployments.</p>
              <ul className="pricing-features">
                <li><Check size={14} /> Everything in Pro</li>
                <li><Check size={14} /> On-premise deployment</li>
                <li><Check size={14} /> SSO / SAML integration</li>
                <li><Check size={14} /> Custom retention policies</li>
                <li><Check size={14} /> Dedicated SLA</li>
                <li><Check size={14} /> Formal verification reports</li>
              </ul>
              <a href="mailto:contact@babylon60.com" className="pricing-cta outline">
                Contact Sales
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ TECH CREDIBILITY ══════════════════ */}
      <section
        className={revealClass(6)}
        ref={(el) => setRef(el, 6)}
        data-reveal-idx="6"
      >
        <div className="landing-tech">
          <div className="section-eyebrow center">UNDER THE HOOD</div>
          <h2 className="features-title">Not another wrapper. Real infrastructure.</h2>
          <div className="tech-grid">
            <div className="tech-item">
              <Globe size={18} />
              <div>
                <strong>Formally verified</strong>
                <span>Core invariants proven in Lean 4. Zero <code>sorry</code> axioms.</span>
              </div>
            </div>
            <div className="tech-item">
              <Shield size={18} />
              <div>
                <strong>Byzantine fault tolerant</strong>
                <span>Fail-fast on hash collision. Silent corruption is impossible.</span>
              </div>
            </div>
            <div className="tech-item">
              <Code size={18} />
              <div>
                <strong>Rust + Python</strong>
                <span>Performance-critical paths in Rust. Developer experience in Python.</span>
              </div>
            </div>
            <div className="tech-item">
              <Lock size={18} />
              <div>
                <strong>AES-256 encryption</strong>
                <span>Data encrypted at rest. Your memories stay yours.</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ══════════════════ FINAL CTA ══════════════════ */}
      <section className="landing-cta-section">
        <h2>Give your agents memory that holds up in court.</h2>
        <p>Start with <code>pip install babylon60</code>. Add lineage when memory starts to matter. Keep both when accountability becomes non-negotiable.</p>
        <div className="hero-actions">
          <button className="landing-cta-primary" onClick={onEnter}>
            Get Started Free <ArrowRight className="cta-icon" />
          </button>
          <a href="https://github.com/borjamoskv/BABYLON-60" target="_blank" rel="noopener noreferrer" className="landing-cta-secondary">
            Explore GitHub →
          </a>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="landing-footer">
        <div className="footer-inner">
          <div className="footer-left">
            <Zap size={16} className="footer-logo" />
            <span>BABYLON-60 © 2026</span>
          </div>
          <div className="footer-links">
            <a href="https://github.com/borjamoskv/BABYLON-60/tree/main/docs">Docs</a>
            <a href="https://github.com/borjamoskv/BABYLON-60/blob/main/docs/api.md">API</a>
            <a href="https://github.com/borjamoskv/BABYLON-60/blob/main/docs/security.md">Security</a>
            <a href="https://github.com/borjamoskv/BABYLON-60">GitHub</a>
          </div>
          <span className="footer-license">MIT OR Apache-2.0</span>
        </div>
      </footer>
    </div>
  );
}
