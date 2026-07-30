import type { DecisionRecord } from '../data/dashboard';

type DecisionTableProps = {
  decisions: DecisionRecord[];
  selectedDecisionId: string;
  activeAgent: string;
  agentOptions: string[];
  onAgentChange: (agent: string) => void;
  onDecisionSelect: (decisionId: string) => void;
};

export function DecisionTable({
  decisions,
  selectedDecisionId,
  activeAgent,
  agentOptions,
  onAgentChange,
  onDecisionSelect,
}: DecisionTableProps) {
  return (
    <div className="table-panel">
      <div className="table-toolbar">
        <div>
          <span className="eyebrow">Decision table</span>
          <h2>High-signal decisions requiring trust review</h2>
        </div>
        <span className="section-meta">Data density tuned for operators</span>
      </div>

      <div className="filter-row" aria-label="Filter decisions by agent">
        {agentOptions.map((agent) => (
          <button
            className="filter-chip"
            data-active={activeAgent === agent}
            key={agent}
            onClick={() => onAgentChange(agent)}
            type="button"
          >
            {agent}
          </button>
        ))}
      </div>

      <div className="table-wrap">
        <table className="decision-table">
          <thead>
            <tr>
              <th>Decision</th>
              <th>Agent</th>
              <th>Status</th>
              <th>Step</th>
              <th>Updated</th>
              <th>Proof</th>
            </tr>
          </thead>
          <tbody>
            {decisions.map((decision) => (
              <tr
                data-active={decision.id === selectedDecisionId}
                key={decision.id}
                onClick={() => onDecisionSelect(decision.id)}
              >
                <td>
                  <div className="decision-table__title">
                    <strong>{decision.title}</strong>
                    <p>{decision.description}</p>
                  </div>
                </td>
                <td>{decision.agent}</td>
                <td>
                  <span className="status-pill" data-tone={decision.statusTone}>
                    {decision.status}
                  </span>
                </td>
                <td>{decision.step}</td>
                <td>{decision.updatedAt}</td>
                <td>{decision.proofSize}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
