export default function HomePage() {
  return (
    <main
      style={{
        minHeight: '100vh',
        background: '#0A0A0A',
        color: '#e0e0e0',
        fontFamily: "'Inter', 'Outfit', system-ui, sans-serif",
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '2rem',
      }}
    >
      <h1
        style={{
          fontSize: 'clamp(2rem, 5vw, 4rem)',
          fontWeight: 800,
          letterSpacing: '-0.03em',
          background: 'linear-gradient(135deg, #2B3BE5 0%, #00ff88 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          textAlign: 'center',
        }}
      >
        CortexPersist Org
      </h1>
      <p
        style={{
          color: '#666',
          fontSize: '1.1rem',
          marginTop: '1rem',
          maxWidth: '600px',
          textAlign: 'center',
          lineHeight: 1.6,
        }}
      >
        Sovereign governance and agentic resource coordination protocol.
      </p>
    </main>
  );
}
