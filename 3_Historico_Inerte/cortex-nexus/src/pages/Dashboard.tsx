import { Link } from 'react-router';
import '../App.css'; // Inheriting global styles

export default function Dashboard() {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a0a',
      color: '#fff',
      fontFamily: '"Outfit", sans-serif',
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '40px',
      backgroundImage: 'radial-gradient(circle at 50% 0%, #1a1a24 0%, #050505 100%)'
    }}>
      <h1 style={{
        fontSize: '48px',
        letterSpacing: '4px',
        fontWeight: 900,
        marginBottom: '10px',
        textTransform: 'uppercase'
      }}>
        CORTEX NEXUS HUB
      </h1>
      <p style={{
        color: '#888',
        fontSize: '18px',
        marginBottom: '60px',
        letterSpacing: '2px'
      }}>
        MATRIZ DE ANÁLISIS DE ENTROPÍA C5-REAL
      </p>

      <div style={{
        display: 'flex',
        gap: '40px',
        maxWidth: '1200px',
        width: '100%',
        justifyContent: 'center',
        flexWrap: 'wrap'
      }}>
        {/* Module A */}
        <Link to="/photobiology" style={{ textDecoration: 'none' }}>
          <div style={{
            background: 'rgba(10, 10, 10, 0.7)',
            backdropFilter: 'blur(16px)',
            borderRadius: '24px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '40px',
            width: '400px',
            height: '300px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transition: 'all 0.3s ease',
            cursor: 'pointer',
            boxShadow: '0 0 40px rgba(227, 38, 54, 0.2)'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 0 60px rgba(227, 38, 54, 0.6)'; e.currentTarget.style.transform = 'scale(1.02)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 0 40px rgba(227, 38, 54, 0.2)'; e.currentTarget.style.transform = 'scale(1)'; }}
          >
            <div>
              <h2 style={{ color: '#e32636', fontSize: '24px', marginBottom: '10px', fontWeight: 900 }}>VECTOR 01: FOTOBIOLOGÍA</h2>
              <p style={{ color: '#ddd', fontSize: '16px', lineHeight: 1.5 }}>
                Teorema Anti-Llorente. Análisis de la misinfodemia sobre los filtros solares y la entropía biológica.
              </p>
            </div>
            <div style={{ color: '#888', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px' }}>
              [ EJECUTAR SIMULACIÓN MP4 ]
            </div>
          </div>
        </Link>

        {/* Module B */}
        <Link to="/substack" style={{ textDecoration: 'none' }}>
          <div style={{
            background: 'rgba(10, 10, 10, 0.7)',
            backdropFilter: 'blur(16px)',
            borderRadius: '24px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '40px',
            width: '400px',
            height: '300px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            transition: 'all 0.3s ease',
            cursor: 'pointer',
            boxShadow: '0 0 40px rgba(46, 80, 144, 0.2)'
          }}
          onMouseEnter={(e) => { e.currentTarget.style.boxShadow = '0 0 60px rgba(46, 80, 144, 0.6)'; e.currentTarget.style.transform = 'scale(1.02)'; }}
          onMouseLeave={(e) => { e.currentTarget.style.boxShadow = '0 0 40px rgba(46, 80, 144, 0.2)'; e.currentTarget.style.transform = 'scale(1)'; }}
          >
            <div>
              <h2 style={{ color: '#2e5090', fontSize: '24px', marginBottom: '10px', fontWeight: 900 }}>VECTOR 02: COGNICIÓN</h2>
              <p style={{ color: '#ddd', fontSize: '16px', lineHeight: 1.5 }}>
                Síndrome Substack (N=10000). Análisis de la entropía semántica y homogeneización creadora.
              </p>
            </div>
            <div style={{ color: '#888', fontSize: '14px', textTransform: 'uppercase', letterSpacing: '1px' }}>
              [ CARGAR INFORME INTERACTIVO ]
            </div>
          </div>
        </Link>
      </div>
    </div>
  );
}
