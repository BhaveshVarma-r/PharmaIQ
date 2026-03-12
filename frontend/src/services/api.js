import axios from 'axios';

const BASE_URL = 'http://localhost:8001';

const api = axios.create({ baseURL: BASE_URL, timeout: 60000 });

export const dashboardAPI = {
  getSummary: () => api.get('/api/dashboard/summary'),
};

export const storesAPI = {
  getAll: (city, tier) =>
    api.get('/api/stores', { params: { city, tier } }),
  getById: (id) => api.get('/api/stores/' + id),
};

export const coldChainAPI = {
  getStatus: () => api.get('/api/cold-chain/status'),
  getStoreDetail: (storeId) =>
    api.get('/api/cold-chain/store/' + storeId),
  getFridgeDetail: (storeId, fridgeId, forceBreach) =>
    api.get('/api/cold-chain/fridge/' + storeId + '/' + fridgeId, {
      params: { force_breach: forceBreach },
    }),
};

export const diseaseAPI = {
  getAlerts: (city) =>
    api.get('/api/disease-alerts', { params: { city } }),
  injectAlert: (data) => api.post('/api/disease-alerts/inject', data),
};

export const inventoryAPI = {
  getNearExpiry: (days, storeId) =>
    api.get('/api/inventory/near-expiry', {
      params: { days, store_id: storeId },
    }),
  getStoreInventory: (storeId) =>
    api.get('/api/inventory/store/' + storeId),
};

export const staffAPI = {
  getSchedule: (storeId, dateStr) =>
    api.get('/api/staff/schedule/' + storeId, {
      params: { date_str: dateStr },
    }),
};

export const agentAPI = {
  runEvent: (data) => api.post('/api/agent/run', data),
  getDecisions: (agent, limit) =>
    api.get('/api/agent/decisions', { params: { agent, limit } }),
};

export const auditAPI = {
  getLog: (limit, eventType) =>
    api.get('/api/audit/log', {
      params: { limit, event_type: eventType },
    }),
  getCritiques: (limit) =>
    api.get('/api/audit/critiques', { params: { limit } }),
  getApprovals: () => api.get('/api/audit/approvals'),
  processApproval: (data) =>
    api.post('/api/audit/approvals/action', data),
};

export const promptsAPI = {
  getRegistry: () => api.get('/api/prompts/registry'),
  validate: () => api.get('/api/prompts/validate'),
  updateVersion: (agent, version) =>
    api.post('/api/prompts/version', { agent, version }),
  getAgentVersions: (agent) =>
    api.get('/api/prompts/' + agent + '/versions'),
};

export const procurementAPI = {
  getOrders: (storeId) =>
    api.get('/api/procurement/orders', {
      params: { store_id: storeId },
    }),
};