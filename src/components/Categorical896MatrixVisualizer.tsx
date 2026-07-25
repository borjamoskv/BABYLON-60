// C5-REAL EXERGY CERTIFIED
import React, { useState, useMemo } from 'react';
import primitivesData from '../primitives.json';

interface PrimitiveData {
  id: number;
  code: string;
  domain_id: string;
  type: string;
  category: string;
  description: string;
  formal_proof_invariant?: string;
}

const DOMAINS = primitivesData.domains || [
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
  const [selectedPrimitiveId, setSelectedPrimitiveId] = useState<number | null>(1);
  const [hoveredPrimitive, setHoveredPrimitive] = useState<number | null>(null);

  // Parse Primitives
  const allPrimitives = useMemo(() => {
    return (primitivesData.primitives || []) as PrimitiveData[];
  }, []);

  // Filter primitives by domain or search
  const filteredPrimitives = useMemo(() => {
    let base = allPrimitives;
    if (searchQuery.trim().length > 0) {
      const q = searchQuery.toLowerCase();
      base = base.filter(p =>
        p.code.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q)
      );
    } else {
      base = base.filter(p => p.domain_id === activeDomain);
    }
    return base;
  }, [allPrimitives, activeDomain, searchQuery]);

  const selectedDomainInfo = DOMAINS.find(d => d.id === activeDomain) || DOMAINS[0];
  const selectedPrimitiveData = allPrimitives.find(p => p.id === selectedPrimitiveId);

  return (
    <div style={{
      backgroundColor: '#0A0A0A',
      color: '#E0E0E0',
      fontFamily: '"Inter", "Roboto", system-ui, sans-serif',
      padding: '24px',
      borderRadius: '12px',
      border: '1px solid #1E255E',
      boxShadow: '0 12px 48px rgba(43, 59, 229, 0.2)',
      position: 'relative',
      overflow: 'hidden'
    }}>
      {/* Background glow artifact */}
      <div style={{
        position: 'absolute',
        top: '-10%',
        right: '-5%',
        width: '300px',
        height: '300px',
        background: 'radial-gradient(circle, rgba(43,59,229,0.1) 0%, rgba(10,10,10,0) 70%)',
        zIndex: 0,
        pointerEvents: 'none'
      }}></div>

      <div style={{ position: 'relative', zIndex: 1 }}>
        {/* Header */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', borderBottom: '1px solid #1A1C29', paddingBottom: '16px' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '22px', color: '#FFFFFF', letterSpacing: '-0.02em', display: 'flex', alignItems: 'center', gap: '10px', fontWeight: '700' }}>
              <span style={{ display: 'inline-block', width: '12px', height: '12px', backgroundColor: '#3B4DFF', borderRadius: '2px', boxShadow: '0 0 10px rgba(59, 77, 255, 0.5)' }}></span>
              MATRIZ CANÓNICA DE 896 PRIMITIVAS
            </h2>
            <span style={{ fontSize: '13px', color: '#B4B9DF', marginTop: '4px', display: 'block' }}>C5-REAL Transducer Engine · Mapeo Topológico</span>
          </div>
          <div style={{
            backgroundColor: 'rgba(59, 77, 255, 0.1)',
            padding: '6px 12px',
            borderRadius: '6px',
            border: '1px solid rgba(59, 77, 255, 0.3)',
            fontSize: '12px',
            color: '#3B4DFF',
            fontWeight: '600',
            fontFamily: 'monospace'
          }}>
            HASH: {primitivesData.cortex_taint?.split(':').pop() || 'aa205d81'}
          </div>
        </div>

        {/* Domain Navigation Tabs */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '24px' }}>
          {DOMAINS.map((dom: any) => {
            const isActive = activeDomain === dom.id;
            return (
              <button
                key={dom.id}
                onClick={() => {
                  setActiveDomain(dom.id);
                  setSearchQuery('');
                  setSelectedPrimitiveId(dom.range[0]);
                }}
                style={{
                  backgroundColor: isActive ? '#3B4DFF' : '#0F1226',
                  color: isActive ? '#FFFFFF' : '#B4B9DF',
                  border: isActive ? '1px solid #4F5EFE' : '1px solid #1E255E',
                  padding: '12px 14px',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '13px',
                  textAlign: 'left',
                  fontWeight: isActive ? '600' : '500',
                  transition: 'all 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
                  boxShadow: isActive ? '0 4px 12px rgba(59, 77, 255, 0.25)' : 'none',
                  outline: 'none'
                }}
                onMouseEnter={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = '#161A36';
                    e.currentTarget.style.borderColor = '#2E3866';
                  }
                }}
                onMouseLeave={(e) => {
                  if (!isActive) {
                    e.currentTarget.style.backgroundColor = '#0F1226';
                    e.currentTarget.style.borderColor = '#1E255E';
                  }
                }}
              >
                <div style={{ marginBottom: '4px' }}>{dom.name}</div>
                <div style={{ fontSize: '11px', opacity: isActive ? 0.9 : 0.6, fontFamily: 'monospace' }}>[{dom.range[0]} - {dom.range[1]}]</div>
              </button>
            );
          })}
        </div>

        {/* Search and Metrics Bar */}
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px' }}>
          <input
            type="text"
            placeholder="Buscar primitiva por firma lógica..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              flex: 1,
              backgroundColor: '#0F1226',
              border: '1px solid #1E255E',
              color: '#FFFFFF',
              padding: '12px 16px',
              borderRadius: '6px',
              fontSize: '14px',
              outline: 'none',
              transition: 'border-color 0.2s ease'
            }}
            onFocus={(e) => e.target.style.borderColor = '#3B4DFF'}
            onBlur={(e) => e.target.style.borderColor = '#1E255E'}
          />
          <div style={{ display: 'flex', alignItems: 'center', gap: '16px', fontSize: '13px', color: '#B4B9DF', backgroundColor: '#0F1226', padding: '0 16px', borderRadius: '6px', border: '1px solid #1E255E' }}>
            <span>Sector: <strong style={{ color: '#FFFFFF' }}>{filteredPrimitives.length} Nodes</strong></span>
            <span style={{ color: '#3B4DFF' }}>|</span>
            <span>{"Complejidad O(1):"} <strong style={{ color: '#10B981' }}>COMPAT(Ω)</strong></span>
          </div>
        </div>

        {/* Interactive Matrix Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(16, 1fr)',
          gap: '8px',
          backgroundColor: '#0F1226',
          padding: '20px',
          borderRadius: '8px',
          border: '1px solid #1E255E',
          boxShadow: 'inset 0 2px 10px rgba(0,0,0,0.2)',
          maxHeight: '400px',
          overflowY: 'auto'
        }}>
          {filteredPrimitives.map((primitive) => {
            const pId = primitive.id;
            const isSelected = selectedPrimitiveId === pId;
            const isHovered = hoveredPrimitive === pId;

            let bgColor = '#161A36';
            let textColor = '#888888';
            let borderColor = '#1E255E';
            let shadow = 'none';
            let transform = 'scale(1)';

            if (isSelected) {
              bgColor = '#3B4DFF';
              textColor = '#FFFFFF';
              borderColor = '#4F5EFE';
              shadow = '0 0 12px rgba(59, 77, 255, 0.6)';
              transform = 'scale(1.05)';
            } else if (isHovered) {
              bgColor = '#2E3866';
              textColor = '#E0E0E0';
              borderColor = '#3B4DFF';
              transform = 'scale(1.02)';
            }

            return (
              <button
                key={pId}
                onClick={() => setSelectedPrimitiveId(pId)}
                onMouseEnter={() => setHoveredPrimitive(pId)}
                onMouseLeave={() => setHoveredPrimitive(null)}
                title={primitive.code}
                style={{
                  backgroundColor: bgColor,
                  color: textColor,
                  border: `1px solid ${borderColor}`,
                  borderRadius: '4px',
                  padding: '10px 0',
                  fontSize: '12px',
                  fontWeight: isSelected ? '700' : '600',
                  fontFamily: 'monospace',
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.15s cubic-bezier(0.4, 0, 0.2, 1)',
                  boxShadow: shadow,
                  transform: transform,
                  zIndex: isSelected ? 10 : 1
                }}
              >
                {String(pId).padStart(3, '0')}
              </button>
            );
          })}
        </div>

        {/* Primitive Detail Inspector */}
        {selectedPrimitiveData && (
          <div style={{
            marginTop: '24px',
            backgroundColor: '#0F1226',
            padding: '20px',
            borderRadius: '8px',
            border: '1px solid #1E255E',
            display: 'flex',
            flexDirection: 'column',
            gap: '12px'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{ width: '8px', height: '8px', backgroundColor: '#10B981', borderRadius: '50%', boxShadow: '0 0 8px rgba(16, 185, 129, 0.6)' }}></div>
              <div style={{ fontSize: '12px', color: '#10B981', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '0.08em' }}>
                CERTIFICACIÓN C5-REAL ACTIVA
              </div>
            </div>

            <div style={{ fontSize: '20px', color: '#FFFFFF', fontWeight: '700', fontFamily: 'monospace', wordBreak: 'break-all' }}>
              [P-{String(selectedPrimitiveData.id).padStart(3, '0')}] :: {selectedPrimitiveData.code}
            </div>

            <div style={{ fontSize: '14px', color: '#B4B9DF', display: 'flex', gap: '16px' }}>
              <span style={{ backgroundColor: '#161A36', padding: '4px 8px', borderRadius: '4px', border: '1px solid #2E3866' }}>Type: {selectedPrimitiveData.type}</span>
              <span style={{ backgroundColor: '#161A36', padding: '4px 8px', borderRadius: '4px', border: '1px solid #2E3866' }}>{selectedPrimitiveData.category}</span>
            </div>

            <div style={{ fontSize: '14px', color: '#E0E0E0', lineHeight: '1.6', backgroundColor: '#0A0B14', padding: '16px', borderRadius: '6px', borderLeft: '3px solid #3B4DFF' }}>
              {selectedPrimitiveData.description}
            </div>

            {selectedPrimitiveData.formal_proof_invariant && (
              <div style={{ fontSize: '12px', color: '#10B981', fontFamily: 'monospace', marginTop: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ display: 'inline-block', width: '4px', height: '14px', backgroundColor: '#10B981' }}></span>
                {selectedPrimitiveData.formal_proof_invariant}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
