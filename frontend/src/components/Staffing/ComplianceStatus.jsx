import React, { useState, useEffect } from 'react';

export default function ComplianceStatus() {
  const [compliance, setCompliance] = useState(null);

  useEffect(() => {
    // Load compliance status from API
  }, []);

  return (
    <div className="compliance-status">
      <h2>Compliance Status</h2>
      {compliance && (
        <div className="compliance-report">
          <div className={`status-badge ${compliance.overallStatus}`}>
            {compliance.overallStatus.toUpperCase()}
          </div>
          <div className="compliance-items">
            {compliance.items.map((item) => (
              <div key={item.id} className={`compliance-item ${item.status}`}>
                <span>{item.name}</span>
                <span className="status">{item.status}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
