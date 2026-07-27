import { Link } from 'react-router';
import '../App.css';

export default function PhotobiologyReport() {
  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0a0a0a',
      color: '#fff',
      fontFamily: '"Outfit", sans-serif',
      display: 'flex',
      flexDirection: 'column',
      padding: '40px',
      backgroundImage: 'radial-gradient(circle at 50% 0%, #1a1a24 0%, #050505 100%)'
    }}>
      
      <div style={{ marginBottom: '40px' }}>
        <Link to="/" style={{ color: '#888', textDecoration: 'none', textTransform: 'uppercase', letterSpacing: '2px', fontWeight: 700 }}>
          &larr; VOLVER AL NEXUS
        </Link>
      </div>

      <div style={{ display: 'flex', gap: '40px', flexWrap: 'wrap' }}>
        
        {/* Left: Video Player */}
        <div style={{ flex: '2', minWidth: '600px' }}>
          <div style={{
            background: 'rgba(10, 10, 10, 0.7)',
            backdropFilter: 'blur(16px)',
            borderRadius: '24px',
            border: '1px solid rgba(227, 38, 54, 0.3)',
            padding: '20px',
            boxShadow: '0 0 60px rgba(227, 38, 54, 0.1)',
            overflow: 'hidden'
          }}>
            <video 
              controls 
              autoPlay 
              style={{ width: '100%', borderRadius: '12px', border: '1px solid #333' }}
            >
              <source src="/assets/video.mp4" type="video/mp4" />
              El autómata no ha encontrado el archivo de video.
            </video>
          </div>
        </div>

        {/* Right: The Theorem */}
        <div style={{ flex: '1', minWidth: '400px' }}>
          <div style={{
            background: 'rgba(10, 10, 10, 0.7)',
            backdropFilter: 'blur(16px)',
            borderRadius: '24px',
            border: '1px solid rgba(255, 255, 255, 0.1)',
            padding: '40px',
            height: '100%'
          }}>
            <h2 style={{ color: '#e32636', fontSize: '28px', marginBottom: '20px', fontWeight: 900, textTransform: 'uppercase' }}>
              Teorema Anti-Llorente
            </h2>
            <div style={{
              background: 'rgba(255,255,255,0.05)',
              padding: '20px',
              borderRadius: '8px',
              fontFamily: 'monospace',
              color: '#d4af37',
              marginBottom: '20px',
              fontSize: '14px'
            }}>
              Claim: "Refutación Estructural del Anti-Sunscreen"<br/>
              Proof: {'{'} Base: "IARC Class 1", Range: [Falsación Absoluta], Confidence: "C5-REAL" {'}'}
            </div>
            
            <p style={{ color: '#ccc', lineHeight: 1.6, fontSize: '16px', marginBottom: '15px' }}>
              <strong>Postulado Fundamental:</strong> La narrativa Anti-Crema Solar (y el negacionismo fotobiológico) es una Alucinación Paramétrica de segunda generación originada por una asimetría en la comprensión de la toxicología (Paracelso) y un bypass narrativo (Green Theater Holístico) que invierte la causalidad termodinámica de la radiación ionizante.
            </p>
            <p style={{ color: '#ccc', lineHeight: 1.6, fontSize: '16px', marginBottom: '15px' }}>
              El Teorema establece que la fotoprotección tópica es el único mecanismo de apantallamiento isomorfo y validado (C5-REAL) para mitigar la entropía del fotodaño.
            </p>
            <p style={{ color: '#ccc', lineHeight: 1.6, fontSize: '16px' }}>
              Exponer el genoma humano a una fuente termonuclear no mitigada (el Sol) basándose en miedo estocástico a moléculas químicas inertes aprobadas regulatorialmente es un fallo catastrófico en la asignación de riesgo causal.
            </p>

          </div>
        </div>

      </div>
    </div>
  );
}
