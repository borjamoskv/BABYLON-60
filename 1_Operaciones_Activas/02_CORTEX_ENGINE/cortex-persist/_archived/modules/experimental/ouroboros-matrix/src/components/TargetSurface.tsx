import { motion } from 'framer-motion';
import { Target, TargetStatus } from '../data/dashboard';
import {
  Target as TargetIcon,
  Search,
  Zap,
  Lock,
  ExternalLink,
  ShieldAlert,
  Terminal
} from 'lucide-react';

interface TargetSurfaceProps {
  targets: Target[];
  isLoading: boolean;
}

const statusColorMap: Record<TargetStatus, string> = {
  discovered: '#2B3BE5', // Babylon60 Blue
  acquired: '#00F0FF',   // Cyber Cyan
  scanning: '#FFD700',   // Warning Gold
  breached: '#FF0033',   // Alert Red
  dismissed: '#444444',  // Muted Grey
};

export function TargetSurface({ targets, isLoading }: TargetSurfaceProps) {
  if (isLoading && targets.length === 0) {
    return (
      <div className="targets-loading">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
        >
          <Search size={48} color="var(--c-accent)" />
        </motion.div>
        <p>Scanning autonomous frontier...</p>
      </div>
    );
  }

  return (
    <div className="target-surface">
      <div className="section-head">
        <div>
          <span className="eyebrow">Frontier Expansion</span>
          <h2>Autonomous Target Surface</h2>
        </div>
        <div className="pulse-indicator">
          <div className="pulse-dot"></div>
          <span>Hunter-Ω Active</span>
        </div>
      </div>

      <div className="targets-grid">
        {targets.map((target, idx) => (
          <motion.div
            key={target.id}
            className="target-card"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: idx * 0.05 }}
            whileHover={{ scale: 1.02 }}
          >
            <div className="target-card__header">
              <div
                className="status-badge"
                style={{ backgroundColor: `${statusColorMap[target.status]}22`, color: statusColorMap[target.status] }}
              >
                {target.status.toUpperCase()}
              </div>
              <div className="threat-level">
                <ShieldAlert size={14} />
                <span>Level {target.threat_level}</span>
              </div>
            </div>

            <div className="target-card__body">
              <h3 className="repo-name">
                <TargetIcon size={16} />
                {target.repo_name}
              </h3>
              <p className="platform-tag">{target.platform} • {target.id}</p>

              <div className="exergy-stat">
                <span className="label">Exergy Potential</span>
                <span className="value">{target.exergy_potential}</span>
              </div>
            </div>

            <div className="target-card__footer">
              <div className="target-actions">
                <button className="btn-icon" title="View Source" onClick={() => window.open(target.repo_url, '_blank')}>
                  <ExternalLink size={16} />
                </button>
                <button className="btn-icon" title="View Local Surface">
                  <Terminal size={16} />
                </button>
              </div>
              <div className="strike-trigger">
                {target.status === 'acquired' || target.status === 'scanning' ? (
                  <motion.div
                    animate={{ opacity: [0.4, 1, 0.4] }}
                    transition={{ duration: 1.5, repeat: Infinity }}
                  >
                    <Zap size={18} color="#00F0FF" />
                  </motion.div>
                ) : target.status === 'breached' ? (
                  <Lock size={18} color="#FF0033" />
                ) : null}
              </div>
            </div>

            {target.status === 'scanning' && (
              <div className="scan-progress-bar">
                <motion.div
                  className="progress-fill"
                  initial={{ width: 0 }}
                  animate={{ width: '100%' }}
                  transition={{ duration: 5, repeat: Infinity }}
                />
              </div>
            )}
          </motion.div>
        ))}

        {targets.length === 0 && (
          <div className="empty-surface">
            <p>No active targets found in the current sector.</p>
          </div>
        )}
      </div>
    </div>
  );
}
