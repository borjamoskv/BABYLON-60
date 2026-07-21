import React, { useState, useMemo } from 'react';

interface PrimitiveData {
  id: number;
  code: string;
  domain_id: string;
  type: string;
  category: string;
  description: string;
}

const DOMAINS = [
  { id: 'D1', name: 'D1: Estructura Categórica Fundamental', range: [1, 112] },
  { id: 'D2', name: 'D2: Límites y Extensiones de Kan', range: [113, 224] },
  { id: 'D3', name: 'D3: Functores, Adjunciones y Mónadas', range: [225, 336] },
  { id: 'D4', name: 'D4: Categorías Monoidales y Enriquecidas', range: [337, 448] },
  { id: 'D5', name: 'D5: Lógica Categórica y Tópoi', range: [449, 560] },
  { id: 'D6', name: 'D6: Colisiones Diagramáticas', range: [561, 672] },
  { id: 'D7', name: 'D7: Antipatrones Categóricos', range: [673, 784] },
  { id: 'D8', name: 'D8: Categorías Fibradas & Métricas', range: [785, 896] }
];

export const Categorical896MatrixVisualizer: React.FC = () => {
  const [activeDomain, setActiveDomain] = useState<string>('D1');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedPrimitive, setSelectedPrimitive] = useState<number | null>(1);

  // Generate domain stats
  const selectedDomainInfo = DOMAINS.find(d => d.id === activeDomain) || DOMAINS[0];

  return (
    <div style={{
      backgroundColor: '#0A0A0A',
      color: '#E0E0E0',
      fontFamily: 'Inter, system-ui, sans-serif',
      padding: '24px',
      borderRadius: '8px',
      border: '1px solid #2B3BE5',
      boxShadow: '0 8px 32px rgba(43, 59, 229, 0.15)'
    }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px', borderBottom: '1px solid #1A1A1A', paddingBottom: '16px' }}>
        <div>
          <h2 style={{ margin: 0, fontSize: '20px', color: '#FFFFFF', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span style={{ display: 'inline-block', width: '10px', height: '10px', backgroundColor: '#2B3BE5', borderRadius: '50%' }}></span>
            MATRIZ CANÓNICA DE 896 PRIMITIVAS CATEGÓRICAS
          </h2>
          <span style={{ fontSize: '12px', color: '#888888' }}>C5-REAL Transducer Engine · Industrial Noir 2026</span>
        </div>
        <div style={{ backgroundColor: '#141414', padding: '6px 12px', borderRadius: '4px', border: '1px solid #222222', fontSize: '12px', color: '#2B3BE5', fontWeight: 'bold' }}>
          SHA256: aa205d81...
        </div>
      </div>

      {/* Domain Navigation Tabs */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '8px', marginBottom: '20px' }}>
        {DOMAINS.map(dom => (
          <button
            key={dom.id}
            onClick={() => setActiveDomain(dom.id)}
            style={{
              backgroundColor: activeDomain === dom.id ? '#2B3BE5' : '#141414',
              color: activeDomain === dom.id ? '#FFFFFF' : '#AAAAAA',
              border: activeDomain === dom.id ? '1px solid #4F5EFE' : '1px solid #222222',
              padding: '10px 12px',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '12px',
              textAlign: 'left',
              fontWeight: activeDomain === dom.id ? '600' : '400',
              transition: 'all 0.15s ease'
            }}
          >
            <div>{dom.name}</div>
            <div style={{ fontSize: '10px', opacity: 0.7, marginTop: '2px' }}>P{dom.range[0]} - P{dom.range[1]}</div>
          </button>
        ))}
      </div>

      {/* Search and Metrics Bar */}
      <div style={{ display: 'flex', gap: '16px', marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Buscar primitiva por código, ID o concepto..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{
            flex: 1,
            backgroundColor: '#141414',
            border: '1px solid #2B2B2B',
            color: '#FFFFFF',
            padding: '10px 14px',
            borderRadius: '4px',
            fontSize: '13px',
            outline: 'none'
          }}
        />
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '13px', color: '#888888' }}>
          <span>Capacidad: <strong style={{ color: '#FFFFFF' }}>112 / 112</strong></span>
          <span>•</span>
          <span>{"Complejidad $\\text{Compat}(\\Omega)$:"} <strong style={{ color: '#2B3BE5' }}>$O(1)$</strong></span>
        </div>
      </div>

      {/* Interactive Matrix Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(16, 1fr)',
        gap: '6px',
        backgroundColor: '#141414',
        padding: '16px',
        borderRadius: '6px',
        border: '1px solid #222222'
      }}>
        {Array.from({ length: 112 }, (_, idx) => {
          const pId = selectedDomainInfo.range[0] + idx;
          const isSelected = selectedPrimitive === pId;
          return (
            <button
              key={pId}
              onClick={() => setSelectedPrimitive(pId)}
              title={`Primitiva P${pId}`}
              style={{
                backgroundColor: isSelected ? '#2B3BE5' : '#1A1A1A',
                color: isSelected ? '#FFFFFF' : '#888888',
                border: isSelected ? '1px solid #FFFFFF' : '1px solid #2A2A2A',
                borderRadius: '3px',
                padding: '8px 0',
                fontSize: '11px',
                fontWeight: '600',
                cursor: 'pointer',
                textAlign: 'center',
                transition: 'all 0.1s ease'
              }}
            >
              {pId}
            </button>
          );
        })}
      </div>

      {/* Primitive Detail Inspector */}
      {selectedPrimitive && (
        <div style={{ marginTop: '20px', backgroundColor: '#111111', padding: '16px', borderRadius: '6px', border: '1px solid #222222' }}>
          <div style={{ fontSize: '11px', color: '#2B3BE5', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            INSPECTOR DE PRIMITIVA CANÓNICA
          </div>
          <div style={{ fontSize: '16px', color: '#FFFFFF', fontWeight: '600', marginTop: '4px' }}>
            P{selectedPrimitive} — {selectedDomainInfo.id} Categorical Primitive #{selectedPrimitive}
          </div>
          <div style={{ fontSize: '13px', color: '#AAAAAA', marginTop: '8px', lineHeight: '1.5' }}>
            {"Primitiva estructural de lógica categórica Nivel-0/1 provista de certificación en $\\mathbf{{Mod}}(\\Sigma, T)$ y acotamiento métrico $\\mu(\\alpha) < \\infty$."}
          </div>
        </div>
      )}
    </div>
  );
};
