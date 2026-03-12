import React, { useState, useEffect } from 'react';

export default function AuditLog() {
  const [logs, setLogs] = useState([]);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    // Load audit logs from API
  }, [filter]);

  return (
    <div className="audit-log">
      <h2>Audit Log</h2>
      <div className="filter-controls">
        <select value={filter} onChange={(e) => setFilter(e.target.value)}>
          <option value="all">All Activities</option>
          <option value="soma">SOMA Actions</option>
          <option value="pulse">PULSE Actions</option>
          <option value="planner">Planner Actions</option>
        </select>
      </div>
      <div className="logs-list">
        {logs.map((log) => (
          <div key={log.id} className="log-entry">
            <span className="timestamp">{log.timestamp}</span>
            <span className="agent">{log.agent}</span>
            <span className="action">{log.action}</span>
            <span className="details">{log.details}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
