import React, { useState } from 'react';

export default function DecisionTrace() {
  const [selectedDecision, setSelectedDecision] = useState(null);
  const [decisions, setDecisions] = useState([]);

  return (
    <div className="decision-trace">
      <h2>Decision Trace</h2>
      <div className="trace-list">
        {decisions.map((decision) => (
          <div
            key={decision.id}
            className="trace-item"
            onClick={() => setSelectedDecision(decision)}
          >
            <h4>{decision.title}</h4>
            <p>Agent: {decision.agent}</p>
            <p>Time: {decision.timestamp}</p>
          </div>
        ))}
      </div>
      {selectedDecision && (
        <div className="trace-detail">
          <h3>{selectedDecision.title}</h3>
          <div className="decision-tree">
            {/* Decision tree visualization will go here */}
          </div>
        </div>
      )}
    </div>
  );
}
