import React, { useState, useEffect } from 'react';

export default function ExpiryTracker() {
  const [expiringItems, setExpiringItems] = useState([]);

  useEffect(() => {
    // Load expiry data from API
  }, []);

  return (
    <div className="expiry-tracker">
      <h2>Product Expiry Tracker</h2>
      <div className="expiry-list">
        {expiringItems.map((item) => (
          <div key={item.id} className={`expiry-item ${item.urgency}`}>
            <div className="product-info">
              <h4>{item.productName}</h4>
              <p>Batch: {item.batchNumber}</p>
            </div>
            <div className="expiry-date">
              <span className="label">Expires:</span>
              <span className="date">{item.expiryDate}</span>
            </div>
            <div className="quantity">
              <span className="label">Qty:</span>
              <span className="amount">{item.quantity} units</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
