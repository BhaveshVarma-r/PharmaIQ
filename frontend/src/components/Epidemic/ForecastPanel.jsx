import React, { useState, useEffect } from 'react';

export default function ForecastPanel() {
  const [forecast, setForecast] = useState(null);

  useEffect(() => {
    // Load forecast data from API
  }, []);

  return (
    <div className="forecast-panel">
      <h2>Epidemic Forecast</h2>
      {forecast && (
        <div className="forecast-content">
          <div className="forecast-item">
            <h3>Peak Date</h3>
            <p>{forecast.peakDate}</p>
          </div>
          <div className="forecast-item">
            <h3>Estimated Cases</h3>
            <p>{forecast.estimatedCases}</p>
          </div>
          <div className="forecast-item">
            <h3>Confidence</h3>
            <p>{forecast.confidence}%</p>
          </div>
        </div>
      )}
    </div>
  );
}
