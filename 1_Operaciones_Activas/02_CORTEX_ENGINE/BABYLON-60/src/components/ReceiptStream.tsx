// C5-REAL EXERGY CERTIFIED
import React from 'react';
import { CheckCircle2, ShieldAlert, Cpu } from 'lucide-react';

export interface ScittReceipt {
  id: string;
  timestamp: string;
  epoch: number;
  digest: string;
  status: 'ATTESTED' | 'HALTED_FAIL_STOP' | 'QUARANTINED';
  latencyMs: number;
  varentropy: number;
}

interface Props {
  receipts: ScittReceipt[];
  onSelectReceipt?: (receipt: ScittReceipt) => void;
}

export const ReceiptStream = ({ receipts, onSelectReceipt }: Props) => {
  return (
    <div className="receipt-stream-panel">
      <div className="section-title">
        <div className="title-with-icon">
          <Cpu size={14} color="#00FF41" />
          <span>SCITT Cryptographic Ledger Stream</span>
        </div>
        <span className="live-pill">LIVE // ZERO COGS</span>
      </div>

      <div className="receipts-list">
        {receipts.map((r) => (
          <div
            key={r.id}
            onClick={() => onSelectReceipt?.(r)}
            className={`receipt-card ${r.status === 'ATTESTED' ? 'receipt-attested' : 'receipt-halted'}`}
          >
            <div className="receipt-top">
              <div className="receipt-status-line">
                {r.status === 'ATTESTED' ? (
                  <CheckCircle2 size={13} color="#00FF41" />
                ) : (
                  <ShieldAlert size={13} color="#FF003C" />
                )}
                <span className="receipt-id">#{r.id}</span>
                <span className="receipt-epoch">Epoch {r.epoch}</span>
              </div>
              <span className="receipt-time">{r.latencyMs.toFixed(2)}ms</span>
            </div>

            <div className="receipt-hash-row">
              <span className="mono-hash">{r.digest}</span>
            </div>

            <div className="receipt-footer">
              <span className="receipt-tag">{r.status}</span>
              <span className="varentropy-tag">Var(H): {(r.varentropy * 100).toFixed(1)}%</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
