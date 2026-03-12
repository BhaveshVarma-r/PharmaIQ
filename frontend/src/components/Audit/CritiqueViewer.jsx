import React, { useState, useEffect } from 'react';

export default function CritiqueViewer() {
  const [critiques, setCritiques] = useState([]);
  const [selectedCritique, setSelectedCritique] = useState(null);

  useEffect(() => {
    // Load critique data from API
  }, []);

  return (
    <div className="critique-viewer">
      <h2>Agent Critique Feedback</h2>
      <div className="critiques-list">
        {critiques.map((critique) => (
          <div
            key={critique.id}
            className={`critique-item ${critique.severity}`}
            onClick={() => setSelectedCritique(critique)}
          >
            <h4>{critique.agent} Feedback</h4>
            <p>{critique.summary}</p>
            <span className={`severity ${critique.severity}`}>{critique.severity}</span>
          </div>
        ))}
      </div>
      {selectedCritique && (
        <div className="critique-detail">
          <h3>Critique: {selectedCritique.agent}</h3>
          <div className="critique-content">
            <p>{selectedCritique.fullAnalysis}</p>
            <div className="recommendations">
              <h4>Recommendations:</h4>
              <ul>
                {selectedCritique.recommendations.map((rec, idx) => (
                  <li key={idx}>{rec}</li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
