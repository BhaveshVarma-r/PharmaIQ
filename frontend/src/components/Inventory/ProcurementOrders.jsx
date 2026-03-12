import React, { useState, useEffect } from 'react';

export default function ProcurementOrders() {
  const [orders, setOrders] = useState([]);

  useEffect(() => {
    // Load procurement orders from API
  }, []);

  return (
    <div className="procurement-orders">
      <h2>Procurement Orders</h2>
      <button>Create New Order</button>
      <div className="orders-list">
        {orders.map((order) => (
          <div key={order.id} className={`order-card ${order.status}`}>
            <div className="order-header">
              <h4>Order #{order.id}</h4>
              <span className={`status-badge ${order.status}`}>{order.status}</span>
            </div>
            <div className="order-details">
              <p>Supplier: {order.supplier}</p>
              <p>Items: {order.itemCount}</p>
              <p>Amount: ${order.amount}</p>
              <p>Expected: {order.expectedDate}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
