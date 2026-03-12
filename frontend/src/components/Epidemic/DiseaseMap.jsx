import React, { useState, useEffect } from 'react';

export default function DiseaseMap() {
  const [diseases, setDiseases] = useState([]);
  const [selectedDisease, setSelectedDisease] = useState(null);

  useEffect(() => {
    // Load disease data from API
  }, []);

  return (
    <div className="disease-map">
      <h2>Disease Distribution Map</h2>
      <div className="disease-controls">
        <select onChange={(e) => setSelectedDisease(e.target.value)}>
          <option>Select Disease</option>
          {diseases.map((disease) => (
            <option key={disease.id} value={disease.id}>
              {disease.name}
            </option>
          ))}
        </select>
      </div>
      {/* Map visualization will be rendered here */}
    </div>
  );
}
