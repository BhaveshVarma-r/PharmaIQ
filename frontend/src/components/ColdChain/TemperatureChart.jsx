import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

export default function TemperatureChart({ fridgeId }) {
  const [data, setData] = useState([]);

  useEffect(() => {
    // Load temperature logs from API
  }, [fridgeId]);

  return (
    <div className="temperature-chart">
      <h3>Temperature History</h3>
      <LineChart width={600} height={300} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="time" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="temperature"
          stroke="#8884d8"
          name="Current Temperature"
        />
        <Line
          type="monotone"
          dataKey="minTemp"
          stroke="#82ca9d"
          name="Min Target"
          strokeDasharray="5 5"
        />
        <Line
          type="monotone"
          dataKey="maxTemp"
          stroke="#ffc658"
          name="Max Target"
          strokeDasharray="5 5"
        />
      </LineChart>
    </div>
  );
}
