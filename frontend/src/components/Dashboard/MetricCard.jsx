import React from 'react';

export default function MetricCard({ title, value, unit, status }) {
  return (
    <div className={`metric-card ${status}`}>
      <h3>{title}</h3>
      <div className="metric-value">
        {value} <span className="unit">{unit}</span>
      </div>
      <div className={`status-indicator ${status}`} />
    </div>
  );
}
