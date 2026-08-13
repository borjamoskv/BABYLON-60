// C5-REAL EXERGY CERTIFIED


export interface EpochSlot {
  id: number;
  status: '0 Idle' | '2 Ready' | '3 Validating' | '4 Active' | '5 Retired' | '6 Quarantine';
  epochId: number;
  readers: number;
  hash: string;
}

interface Props {
  slots: EpochSlot[];
  activeEpochPtr: number;
  fallbackEpochPtr: number;
}

export const RingBufferVisualizer: React.FC<Props> = ({ slots, activeEpochPtr, fallbackEpochPtr }) => {
  return (
    <div className="ring-buffer-container">
      <div className="section-title">
        <span>Shared Memory Manifest (Lock-Free EBR)</span>
        <span className="badge-mono">0x10000000 (Header + 8 Slots)</span>
      </div>

      <div className="slots-grid">
        {slots.map((slot) => {
          const isActive = slot.id === activeEpochPtr;
          const isFallback = slot.id === fallbackEpochPtr;
          let statusClass = 'status-idle';
          if (slot.status.includes('Active')) statusClass = 'status-active';
          else if (slot.status.includes('Validating')) statusClass = 'status-val';
          else if (slot.status.includes('Quarantine')) statusClass = 'status-quarantine';
          else if (slot.status.includes('Retired')) statusClass = 'status-retired';

          return (
            <div
              key={slot.id}
              className={`slot-card ${statusClass} ${isActive ? 'ring-active' : ''} ${isFallback ? 'ring-fallback' : ''}`}
            >
              <div className="slot-header">
                <span className="slot-index">SLOT #{slot.id}</span>
                {isActive && <span className="tag-active">ACTIVE (E)</span>}
                {isFallback && <span className="tag-fallback">FALLBACK (E-1)</span>}
              </div>

              <div className="slot-body">
                <div className="slot-field">
                  <span className="field-label">Epoch:</span>
                  <span className="field-val">#{slot.epochId}</span>
                </div>
                <div className="slot-field">
                  <span className="field-label">State:</span>
                  <span className="field-val">{slot.status}</span>
                </div>
                <div className="slot-field">
                  <span className="field-label">Readers:</span>
                  <span className="field-val">{slot.readers}</span>
                </div>
                <div className="slot-field">
                  <span className="field-label">SHA3:</span>
                  <span className="field-hash">{slot.hash.slice(0, 10)}...</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
