import './App.css'

function App() {
  return (
    <div className="app-container">
      <header className="hero">
        <h1 className="heading-gradient">BABYLON-60</h1>
        <p>The formal fortress against unbounded digital entropy. A mathematically pure orchestration engine.</p>
        <button className="btn-primary">Initialize Kernel</button>
      </header>

      <main className="grid-features">
        <div className="glass-panel feature-card">
          <h3>BFT Fail-Fast</h3>
          <p>Strict memory invariants prevent silent causality overwrites. We abort before entropy diverges.</p>
          <div className="code-block">
            <code>panic!("Fail-fast: INV_BFT_04 Collision");</code>
          </div>
        </div>

        <div className="glass-panel feature-card">
          <h3>L1 Thermodynamic Anchor</h3>
          <p>Absolute entropy commitment anchored natively to Bitcoin's Proof of Work via raw 32-byte Merkle Roots.</p>
          <div className="code-block">
            <code>graph.sha256 = 5eea556d...</code>
          </div>
        </div>

        <div className="glass-panel feature-card">
          <h3>Zero-Worktree Scalability</h3>
          <p>In-memory BFT actors orchestrating asynchronous swarm scaling without ENOSPC vulnerabilities.</p>
          <div className="code-block">
            <code>queue.push_back(Coroutine);</code>
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
