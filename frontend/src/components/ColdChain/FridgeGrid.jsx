import React from 'react';

export default function FridgeGrid({ unit }) {
  const fridges = unit.refrigerators || [];

  return (
    <div className="fridge-grid">
      <h2>{unit.name} - Refrigeration Units</h2>
      <div className="grid">
        {fridges.map((fridge) => (
          <div key={fridge.id} className={`fridge-card ${fridge.status}`}>
            <h3>{fridge.name}</h3>
            <div className="temperature">
              <span className="value">{fridge.temperature}°C</span>
              <span className="status">{fridge.status}</span>
            </div>
            <div className="capacity">
              {fridge.usedCapacity} / {fridge.totalCapacity} units
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
