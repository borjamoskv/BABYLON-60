// @C5-REAL
/* custom-cursor */
import React, { useState, useMemo } from 'react';

interface SubstackNode {
  post_id: number;
  title: string;
  date: string;
  wordcount: number;
  exergy_score: number;
  status: string;
}

interface SubstackLedgerProps {
  initialNodes: SubstackNode[];
}

export default function SubstackLedger({ initialNodes }: SubstackLedgerProps) {
  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState<string>('ALL');
  const [visibleCount, setVisibleCount] = useState(15);

  // Helper to categorize post based on title
  const getCategory = (title: string): 'TECH' | 'CRYPTO' | 'MUSIC' | 'PHILOSOPHY' | 'GENERAL' => {
    const t = title.toLowerCase();
    if (
      /\b(ia|bot|openai|embeddings|antigravity|xokas|programadores|senior|babylon60|algorithm|software|desarrollo|ast|isa|genoma|linter|prompt|claud|gpt|ollama|engine|mcp)\b/.test(t) ||
      t.includes('babylon60') ||
      t.includes('agent') ||
      t.includes('editor') ||
      t.includes('alzheimer')
    ) {
      return 'TECH';
    }
    if (/\b(domains|ens|unstoppable|phishing|drainer|eip|crypto|blockchain|tokens|defi|wallet|ethereum|solana)\b/.test(t)) {
      return 'CRYPTO';
    }
    if (
      /\b(deftones|nine inch|manos de topo|raveros|rave|música|dj|vj|auditoría|kase\.o|camisa|compuesto|sonido|beat|audio|pcm|canción|acústica)\b/.test(t)
    ) {
      return 'MUSIC';
    }
    if (
      /\b(excepción|regla|inmanencia|singularidad|epistémica|matemáticas|conspiración|indignación|wifi|coherencia|pensar|humana|extincion|pensamiento|filosofía|realidad|mentira|influencer|lujo)\b/.test(t)
    ) {
      return 'PHILOSOPHY';
    }
    return 'GENERAL';
  };

  const getEmoji = (title: string, category: string): string => {
    const t = title.toLowerCase();
    if (t.includes('phishing') || t.includes('drainer') || t.includes('forense')) return '🛡️';
    if (t.includes('deftones') || t.includes('nine inch')) return '🎹';
    if (category === 'TECH') return '🤖';
    if (category === 'CRYPTO') return '🐐';
    if (category === 'MUSIC') return '🎧';
    if (category === 'PHILOSOPHY') return '📐';
    return '🧬';
  };

  // Process & enrich nodes
  const processedNodes = useMemo(() => {
    return initialNodes
      .map(node => {
        const category = getCategory(node.title);
        const emoji = getEmoji(node.title, category);
        return {
          ...node,
          category,
          emoji,
        };
      })
      .sort((a, b) => new Date(b.date).getTime() - new Date(a.date).getTime());
  }, [initialNodes]);

  // Statistics
  const stats = useMemo(() => {
    const totalExergy = processedNodes.reduce((acc, node) => acc + (node.exergy_score || 0), 0);
    const avgExergy = processedNodes.length > 0 ? Math.round(totalExergy / processedNodes.length) : 0;
    const totalWords = processedNodes.reduce((acc, node) => acc + (node.wordcount || 0), 0);
    return {
      totalNodes: processedNodes.length,
      avgExergy,
      totalWords,
    };
  }, [processedNodes]);

  // Filter nodes
  const filteredNodes = useMemo(() => {
    return processedNodes.filter(node => {
      const matchesSearch = node.title.toLowerCase().includes(search.toLowerCase());
      const matchesCategory = selectedCategory === 'ALL' || node.category === selectedCategory;
      return matchesSearch && matchesCategory;
    });
  }, [processedNodes, search, selectedCategory]);

  const displayedNodes = useMemo(() => {
    return filteredNodes.slice(0, visibleCount);
  }, [filteredNodes, visibleCount]);

  const formatDate = (dateStr: string) => {
    try {
      const date = new Date(dateStr);
      return date.toISOString().split('T')[0];
    } catch {
      return dateStr;
    }
  };

  return (
    <div className="substack-ledger">
      {/* Styles Injection */}
      <style dangerouslySetInnerHTML={{ __html: `
        .substack-ledger {
          margin-top: 4rem;
          font-family: 'Inter', sans-serif;
        }
        .ledger-stats {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2.5rem;
        }
        .stat-card {
          background: rgba(10, 10, 10, 0.4);
          border: 1px solid rgba(43, 59, 229, 0.15);
          padding: 1.5rem;
          border-radius: 8px;
          backdrop-filter: blur(10px);
          text-align: left;
          position: relative;
          overflow: hidden;
          transition: border-color 0.3s ease;
        }
        .stat-card:hover {
          border-color: rgba(43, 59, 229, 0.35);
        }
        .stat-card::before {
          content: '';
          position: absolute;
          left: 0; top: 0; bottom: 0; width: 3px;
          background: var(--yinmn-blue, #2b3be5);
          opacity: 0.5;
        }
        .stat-card.neon::before {
          background: #00e5a3;
        }
        .stat-label {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.7rem;
          color: rgba(224, 224, 224, 0.5);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          margin-bottom: 0.5rem;
        }
        .stat-value {
          font-family: 'Space Grotesk', sans-serif;
          font-size: 1.8rem;
          font-weight: 700;
          color: #ffffff;
        }
        .stat-value.neon-glow {
          color: #00e5a3;
          text-shadow: 0 0 10px rgba(0, 229, 163, 0.4);
        }
        .ledger-controls {
          display: flex;
          flex-direction: column;
          gap: 1rem;
          margin-bottom: 2rem;
        }
        @media (min-width: 768px) {
          .ledger-controls {
            flex-direction: row;
            justify-content: space-between;
            align-items: center;
          }
        }
        .ledger-search {
          background: rgba(0, 0, 0, 0.5);
          border: 1px solid rgba(43, 59, 229, 0.2);
          color: #ffffff;
          padding: 0.8rem 1.2rem;
          border-radius: 8px;
          font-family: 'Inter', sans-serif;
          font-size: 0.9rem;
          width: 100%;
          max-width: 400px;
          outline: none;
          transition: border-color 0.3s ease, box-shadow 0.3s ease;
        }
        .ledger-search:focus {
          border-color: rgba(43, 59, 229, 0.6);
          box-shadow: 0 0 15px rgba(43, 59, 229, 0.25);
        }
        .ledger-filters {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }
        .filter-btn {
          background: rgba(255, 255, 255, 0.02);
          border: 1px solid rgba(255, 255, 255, 0.08);
          color: rgba(224, 224, 224, 0.6);
          padding: 0.5rem 1.0rem;
          border-radius: 6px;
          cursor: pointer;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.75rem;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          transition: all 0.2s ease;
        }
        .filter-btn:hover {
          background: rgba(43, 59, 229, 0.08);
          color: #ffffff;
          border-color: rgba(43, 59, 229, 0.3);
        }
        .filter-btn.active {
          background: rgba(43, 59, 229, 0.2);
          color: #ffffff;
          border-color: rgba(43, 59, 229, 0.8);
          box-shadow: 0 0 15px rgba(43, 59, 229, 0.2);
        }
        .ledger-table-header {
          display: grid;
          grid-template-columns: 100px 1fr 100px 160px 150px;
          padding: 1rem 1.5rem;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.75rem;
          color: rgba(224, 224, 224, 0.4);
          text-transform: uppercase;
          letter-spacing: 0.1em;
          border-bottom: 1px solid rgba(255, 255, 255, 0.08);
        }
        @media (max-width: 768px) {
          .ledger-table-header {
            display: none;
          }
        }
        .ledger-list {
          background: rgba(10, 10, 12, 0.94);
          border: 1px solid rgba(43, 59, 229, 0.2);
          border-radius: 8px;
          overflow: hidden;
          box-shadow: 0 28px 80px rgba(0, 0, 0, 0.5);
        }
        .ledger-row {
          display: grid;
          grid-template-columns: 100px 1fr 100px 160px 150px;
          align-items: center;
          padding: 1.25rem 1.5rem;
          border-bottom: 1px solid rgba(255, 255, 255, 0.04);
          transition: background-color 0.2s ease, border-color 0.2s ease;
        }
        .ledger-row:hover {
          background: rgba(43, 59, 229, 0.04);
          border-color: rgba(43, 59, 229, 0.2);
        }
        @media (max-width: 768px) {
          .ledger-row {
            grid-template-columns: 1fr;
            gap: 0.8rem;
            padding: 1.25rem;
          }
        }
        .ledger-date {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.8rem;
          color: rgba(224, 224, 224, 0.4);
        }
        .ledger-title-group {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }
        .ledger-emoji {
          font-size: 1.1rem;
        }
        .ledger-title-link {
          font-family: 'Space Grotesk', sans-serif;
          font-weight: 500;
          font-size: 1rem;
          color: #ffffff;
          text-decoration: none;
          transition: color 0.2s ease;
          line-height: 1.3;
        }
        .ledger-title-link:hover {
          color: #2b3be5;
        }
        .ledger-wordcount {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.8rem;
          color: rgba(224, 224, 224, 0.5);
        }
        .ledger-exergy {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }
        .exergy-bar-bg {
          width: 70px;
          height: 6px;
          background: rgba(255, 255, 255, 0.05);
          border-radius: 3px;
          overflow: hidden;
        }
        .exergy-bar-fg {
          height: 100%;
          background: linear-gradient(90deg, #2b3be5, #ff0055);
        }
        .exergy-score-text {
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.8rem;
          font-weight: 600;
          color: #ff0055;
        }
        .ledger-status-badge {
          display: inline-block;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.7rem;
          padding: 0.25rem 0.6rem;
          border-radius: 4px;
          border: 1px solid rgba(43, 59, 229, 0.4);
          color: rgba(224, 224, 224, 0.7);
          background: rgba(43, 59, 229, 0.05);
          text-align: center;
          letter-spacing: 0.05em;
        }
        .ledger-status-badge.synergized {
          border-color: rgba(0, 229, 163, 0.3);
          color: #00e5a3;
          background: rgba(0, 229, 163, 0.02);
          box-shadow: 0 0 10px rgba(0, 229, 163, 0.05);
        }
        .ledger-status-badge.singularity {
          border-color: rgba(255, 159, 28, 0.4);
          color: #ff9f1c;
          background: rgba(255, 159, 28, 0.03);
          box-shadow: 0 0 10px rgba(255, 159, 28, 0.05);
        }
        .load-more-container {
          display: flex;
          justify-content: center;
          margin-top: 2rem;
        }
        .load-more-btn {
          background: transparent;
          border: 1px solid rgba(43, 59, 229, 0.4);
          color: #ffffff;
          padding: 0.8rem 2.5rem;
          border-radius: 999px;
          cursor: pointer;
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.8rem;
          text-transform: uppercase;
          letter-spacing: 0.1em;
          transition: all 0.3s ease;
        }
        .load-more-btn:hover {
          background: rgba(43, 59, 229, 0.15);
          border-color: rgba(43, 59, 229, 0.8);
          box-shadow: 0 0 15px rgba(43, 59, 229, 0.25);
        }
        .ledger-empty {
          padding: 4rem;
          text-align: center;
          color: rgba(224, 224, 224, 0.5);
          font-family: 'IBM Plex Mono', monospace;
          font-size: 0.9rem;
          letter-spacing: 0.05em;
        }
      ` }} />

      {/* Statistics Cards */}
      <div className="ledger-stats">
        <div className="stat-card">
          <div className="stat-label">Reality Assertions</div>
          <div className="stat-value">C5-REAL</div>
        </div>
        <div className="stat-card neon">
          <div className="stat-label">Causal Nodes</div>
          <div className="stat-value neon-glow">{stats.totalNodes}</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Avg Exergy Yield</div>
          <div className="stat-value">{stats.avgExergy} EX</div>
        </div>
        <div className="stat-card">
          <div className="stat-label">Entropy Pruned</div>
          <div className="stat-value">{(stats.totalWords / 1000).toFixed(1)}k Words</div>
        </div>
      </div>

      {/* Filters and Search */}
      <div className="ledger-controls">
        <input
          type="text"
          className="ledger-search"
          placeholder="Filter causal nodes by title..."
          value={search}
          onChange={e => {
            setSearch(e.target.value);
            setVisibleCount(15);
          }}
        />
        <div className="ledger-filters">
          {['ALL', 'TECH', 'CRYPTO', 'MUSIC', 'PHILOSOPHY'].map(cat => (
            <button
              key={cat}
              className={`filter-btn ${selectedCategory === cat ? 'active' : ''}`}
              onClick={() => {
                setSelectedCategory(cat);
                setVisibleCount(15);
              }}
            >
              {cat}
            </button>
          ))}
        </div>
      </div>

      {/* Ledger Table */}
      <div className="ledger-list">
        <div className="ledger-table-header">
          <div>Timestamp</div>
          <div>Causal Node / Title</div>
          <div>Words</div>
          <div>Exergy Density</div>
          <div>Authentication</div>
        </div>

        {displayedNodes.length === 0 ? (
          <div className="ledger-empty">
            No causal nodes matching filters found.
          </div>
        ) : (
          displayedNodes.map(node => (
            <div key={node.post_id} className="ledger-row">
              <div className="ledger-date">{formatDate(node.date)}</div>
              <div className="ledger-title-group">
                <span className="ledger-emoji">{node.emoji}</span>
                <a
                  href={`https://borjamoskv.substack.com/p/${node.post_id}`}
                  className="ledger-title-link"
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  {node.title}
                </a>
              </div>
              <div className="ledger-wordcount">{node.wordcount} w</div>
              <div className="ledger-exergy">
                <div className="exergy-bar-bg" title={`${node.exergy_score} EX`}>
                  <div
                    className="exergy-bar-fg"
                    style={{ width: `${(node.exergy_score / 1000) * 100}%` }}
                  />
                </div>
                <span className="exergy-score-text">{node.exergy_score}</span>
              </div>
              <div>
                <span className={`ledger-status-badge ${
                  node.status === 'C5-REAL_SYNERGIZED' ? 'synergized' :
                  node.status === 'C5-REAL_SINGULARITY' ? 'singularity' : ''
                }`}>
                  {node.status}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Load More button */}
      {filteredNodes.length > visibleCount && (
        <div className="load-more-container">
          <button
            className="load-more-btn"
            onClick={() => setVisibleCount(prev => prev + 15)}
          >
            Load Next Nodes ➔
          </button>
        </div>
      )}
    </div>
  );
}
