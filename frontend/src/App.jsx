import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { useEffect } from 'react';
import { wsClient } from './services/websocket';
import { usePharmaStore } from './store/pharmaStore';
import Sidebar from './components/shared/Sidebar';
import DashboardPage from './pages/DashboardPage';
import ColdChainPage from './pages/ColdChainPage';
import EpidemicPage from './pages/EpidemicPage';
import StaffingPage from './pages/StaffingPage';
import InventoryPage from './pages/InventoryPage';
import AuditPage from './pages/AuditPage';
import PromptsPage from './pages/PromptsPage';

export default function App() {
  const {
    addAlert,
    setAgentResult,
    updateSensorReading,
    incrementBreachCount,
    incrementLowStockCount,
    updateLiveStats,
  } = usePharmaStore();

  useEffect(() => {
    wsClient.connect();

    const offBreach = wsClient.on('breach_alert', (data) => {
      addAlert(data);
      incrementBreachCount();
    });
    const offSensor = wsClient.on('sensor_reading', (data) => {
      updateSensorReading(data.store_id, data.fridge_id, data);
    });
    const offLowStock = wsClient.on('low_stock_alert', (data) => {
      addAlert(data);
      incrementLowStockCount();
    });
    const offInventory = wsClient.on('inventory_update', (data) => {
      updateLiveStats({ lastInventoryUpdate: data.timestamp });
    });
    const offDelivered = wsClient.on('order_delivered', (data) => {
      addAlert({ ...data, type: 'order_delivered' });
    });
    const offNewAlert = wsClient.on('new_disease_alert', (data) => {
      addAlert(data);
    });
    const offEscalated = wsClient.on('alert_escalated', (data) => {
      addAlert(data);
    });
    const offResolved = wsClient.on('alert_resolved', (data) => {
      addAlert({ ...data, type: 'alert_resolved' });
    });
    const offExpiry = wsClient.on('expiry_alert', (data) => {
      if (data.near_expiry_count > 0) {
        addAlert({
          ...data,
          message: data.near_expiry_count + ' items approaching expiry',
        });
      }
    });
    const offAgentComplete = wsClient.on('agent_complete', (data) => {
      if (data.event_id) {
        setAgentResult(data.event_id, data.result);
      }
    });

    return () => {
      offBreach();
      offSensor();
      offLowStock();
      offInventory();
      offDelivered();
      offNewAlert();
      offEscalated();
      offResolved();
      offExpiry();
      offAgentComplete();
      wsClient.disconnect();
    };
  }, []);

  return (
    <BrowserRouter>
      <div className="flex h-screen bg-gray-50 overflow-hidden">
        <Sidebar />
        <div className="flex-1 flex flex-col ml-64 overflow-hidden">
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/cold-chain" element={<ColdChainPage />} />
            <Route path="/epidemic" element={<EpidemicPage />} />
            <Route path="/staffing" element={<StaffingPage />} />
            <Route path="/inventory" element={<InventoryPage />} />
            <Route path="/audit" element={<AuditPage />} />
            <Route path="/prompts" element={<PromptsPage />} />
          </Routes>
        </div>
      </div>
    </BrowserRouter>
  );
}