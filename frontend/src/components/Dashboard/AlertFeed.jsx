import React, { useState, useEffect } from 'react';

export default function AlertFeed() {
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    // Load alerts from API
  }, []);

  return (
    <div className="alert-feed">
      <h2>Alert Feed</h2>
      <ul className="alerts-list">
        {alerts.map((alert) => (
          <li key={alert.id} className={`alert ${alert.severity}`}>
            <span className="timestamp">{alert.timestamp}</span>
            <span className="message">{alert.message}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
