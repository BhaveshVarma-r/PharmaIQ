import { create } from 'zustand';

export const usePharmaStore = create((set) => ({
  liveAlerts: [],
  sensorReadings: {},
  agentResults: {},
  isProcessing: false,
  liveStats: {
    breachCount: 0,
    lowStockCount: 0,
    activeAlertCount: 0,
    ordersDelivered: 0,
    lastInventoryUpdate: null,
  },

  addAlert: (alert) =>
    set((state) => ({
      liveAlerts: [
        { ...alert, id: Date.now() + Math.random() },
        ...state.liveAlerts,
      ].slice(0, 100),
    })),

  clearAlert: (id) =>
    set((state) => ({
      liveAlerts: state.liveAlerts.filter((a) => a.id !== id),
    })),

  clearAllAlerts: () => set({ liveAlerts: [] }),

  updateSensorReading: (storeId, fridgeId, data) =>
    set((state) => ({
      sensorReadings: {
        ...state.sensorReadings,
        [storeId + '_' + fridgeId]: { ...data, updatedAt: Date.now() },
      },
    })),

  setAgentResult: (eventId, result) =>
    set((state) => ({
      agentResults: { ...state.agentResults, [eventId]: result },
      isProcessing: false,
    })),

  setProcessing: (v) => set({ isProcessing: v }),

  incrementBreachCount: () =>
    set((state) => ({
      liveStats: {
        ...state.liveStats,
        breachCount: state.liveStats.breachCount + 1,
      },
    })),

  incrementLowStockCount: () =>
    set((state) => ({
      liveStats: {
        ...state.liveStats,
        lowStockCount: state.liveStats.lowStockCount + 1,
      },
    })),

  updateLiveStats: (updates) =>
    set((state) => ({
      liveStats: { ...state.liveStats, ...updates },
    })),
}));