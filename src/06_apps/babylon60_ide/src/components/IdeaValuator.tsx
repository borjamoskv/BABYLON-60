// C5-REAL EXERGY CERTIFIED
import { useState } from 'react';
import { Target, Zap } from 'lucide-react';

export function IdeaValuator() {
  const [idea, setIdea] = useState('');
  const [isEvaluating, setIsEvaluating] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [progress, setProgress] = useState(0);
  const targetScore = 21000;

  const handleEvaluate = () => {
    if (!idea.trim() || isEvaluating) return;
    setIsEvaluating(true);

    // Start from a random baseline between 1000 and 5000
    const startScore = Math.floor(Math.random() * 4000) + 1000;
    setScore(startScore);
    setProgress(0);

    // Animate up to 21000
    let current = startScore;
    const interval = setInterval(() => {
      current += Math.floor(Math.random() * 500) + 100; // Increment
      if (current >= targetScore) {
        current = targetScore;
        clearInterval(interval);
        setIsEvaluating(false);
      }
      setScore(current);
      setProgress((current / targetScore) * 100);
    }, 50);
  };

  return (
    <div className="idea-valuator">
      <div className="valuator-header">
        <Target size={14} color="#00FF41" />
        <span>C5-REAL EXERGY VALUATOR</span>
      </div>

      <div className="valuator-input-area">
        <textarea
          value={idea}
          onChange={(e) => setIdea(e.target.value)}
          placeholder="Introduce tu idea para calcular su valor exergético..."
          className="valuator-input"
          rows={3}
        />
        <button
          onClick={handleEvaluate}
          className={`valuator-btn ${isEvaluating ? 'evaluating' : ''}`}
          disabled={isEvaluating || !idea.trim()}
        >
          <Zap size={16} />
          {isEvaluating ? 'ITERANDO...' : 'VALORAR IDEA'}
        </button>
      </div>

      {score !== null && (
        <div className="valuator-result">
          <div className="score-display">
            <span className="score-label">VALOR ESTIMADO:</span>
            <span className={`score-value ${score === targetScore ? 'max-score' : ''}`}>
              {score.toLocaleString()} / 21,000
            </span>
          </div>
          <div className="progress-bar-bg">
            <div
              className="progress-bar-fill"
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          {score === targetScore && (
            <div className="max-reached-alert">
              ÓPTIMO EXERGÉTICO ALCANZADO (21,000)
            </div>
          )}
        </div>
      )}
    </div>
  );
}
