// C5-REAL EXERGY CERTIFIED
import { Cpu, Users, Hash, ShieldCheck, AlertTriangle, RefreshCw } from 'lucide-react';

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
  onSlotClick?: (slot: EpochSlot) => void;
}

export const RingBufferVisualizer = ({
  slots,
  activeEpochPtr,
  fallbackEpochPtr,
  onSlotClick,
}: Props) => {
  return (
    <div className="ring-buffer-container">
      {/* Header */}
      <div className="ring-buffer-header">
        <div className="title-with-icon">
          <Cpu size={14} color="#00FF41" />
          <span className="section-title-text">
            Shared Memory Ring Buffer (Lock-Free Epoch Reclamation)
          </span>
        </div>
        <div className="ring-header-tags">
          <span className="badge-mono">BASE: 0x10000000</span>
          <span className="badge-mono">SLOT SIZE: 4096B</span>
          <span className="badge-atomic">ATOMIC PTR CAS (Ring-0)</span>
        </div>
      </div>

      {/* 8-Slot Memory Grid */}
      <div className="slots-grid">
        {slots.map((slot) => {
          const isActive = slot.id === activeEpochPtr;
          const isFallback = slot.id === fallbackEpochPtr;
          const offsetHex = `0x${(0x10000000 + slot.id * 4096).toString(16).toUpperCase()}`;

          let statusClass = 'status-idle';
          let statusIcon = null;

          if (slot.status.includes('Active')) {
            statusClass = 'status-active';
            statusIcon = <ShieldCheck size={12} color="#00FF41" />;
          } else if (slot.status.includes('Validating')) {
            statusClass = 'status-val';
            statusIcon = <RefreshCw size={12} color="#FFAA00" className="spin-slow" />;
          } else if (slot.status.includes('Quarantine')) {
            statusClass = 'status-quarantine';
            statusIcon = <AlertTriangle size={12} color="#FF003C" />;
          } else if (slot.status.includes('Retired')) {
            statusClass = 'status-retired';
          }

          return (
            <div
              key={slot.id}
              onClick={() => onSlotClick?.(slot)}
              className={`slot-card ${statusClass} ${isActive ? 'ring-active' : ''} ${isFallback ? 'ring-fallback' : ''}`}
            >
              {/* Slot Header */}
              <div className="slot-header">
                <div className="slot-id-wrap">
                  <span className="slot-index">SLOT #{slot.id}</span>
                  <span className="slot-offset">{offsetHex}</span>
                </div>
                {isActive && <span className="tag-active">ACTIVE (E)</span>}
                {isFallback && !isActive && <span className="tag-fallback">FALLBACK (E-1)</span>}
              </div>

              {/* Slot Body */}
              <div className="slot-body">
                <div className="slot-field">
                  <span className="field-label">
                    <Hash size={10} /> Epoch:
                  </span>
                  <span className="field-val">#{slot.epochId}</span>
                </div>

                <div className="slot-field">
                  <span className="field-label">Status:</span>
                  <span className="field-val-status">
                    {statusIcon}
                    <span>{slot.status}</span>
                  </span>
                </div>

                <div className="slot-field">
                  <span className="field-label">
                    <Users size={10} /> Readers:
                  </span>
                  <span className="field-val readers-badge">{slot.readers}</span>
                </div>

                <div className="slot-field">
                  <span className="field-label">SHA3 Digest:</span>
                  <span className="field-hash">{slot.hash.slice(0, 8)}...</span>
                </div>
              </div>

              {/* Progress bar for reader safety */}
              <div className="slot-footer-bar">
                <div
                  className="readers-progress"
                  style={{
                    width: `${Math.min(slot.readers * 25, 100)}%`,
                    backgroundColor: slot.readers > 0 ? '#00FF41' : 'rgba(255,255,255,0.1)',
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
