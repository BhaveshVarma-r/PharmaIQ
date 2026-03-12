import { useState, useCallback } from 'react';
import { diseaseAPI, agentAPI } from '../services/api';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import StatusBadge from '../components/shared/StatusBadge';
import { Activity, MapPin, Play, PlusCircle, RefreshCw } from 'lucide-react';
import { usePharmaStore } from '../store/pharmaStore';

const CITIES = [
  'Delhi', 'Mumbai', 'Bangalore', 'Chennai',
  'Kolkata', 'Hyderabad', 'Pune',
];
const DISEASES = ['dengue', 'malaria', 'influenza', 'cholera', 'typhoid'];
const ALERT_LEVELS = ['WATCH', 'ALERT', 'OUTBREAK'];

const LEVEL_STYLES = {
  WATCH: 'bg-blue-50 border-blue-200',
  ALERT: 'bg-amber-50 border-amber-200',
  OUTBREAK: 'bg-orange-50 border-orange-200',
  EPIDEMIC: 'bg-red-50 border-red-200',
};

export default function EpidemicPage() {
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentResult, setAgentResult] = useState(null);
  const [runningAlertId, setRunningAlertId] = useState(null);
  const [injectCity, setInjectCity] = useState('Delhi');
  const [injectDisease, setInjectDisease] = useState('dengue');
  const [injectLevel, setInjectLevel] = useState('ALERT');
  const { agentResults } = usePharmaStore();

  const fetchAlerts = useCallback(() => diseaseAPI.getAlerts(), []);

  const { data: alertsData, refresh } = useAutoRefresh(
    fetchAlerts,
    60000,
    ['new_disease_alert', 'alert_escalated', 'alert_resolved', 'disease_update']
  );

  const alerts = alertsData?.alerts || [];

  const injectAlert = async () => {
    await diseaseAPI.injectAlert({
      city: injectCity,
      disease: injectDisease,
      alert_level: injectLevel,
    });
    refresh();
  };

  const runPULSE = async (alert) => {
    setAgentRunning(true);
    setRunningAlertId(alert.alert_id);
    setAgentResult(null);
    try {
      await agentAPI.runEvent({
        event_type: 'epidemic_alert',
        disease_alert: alert,
      });
      const checkResult = () => {
        const results = usePharmaStore.getState().agentResults;
        const found = Object.values(results).find(
          (v) => v && v.event_type === 'epidemic_alert'
        );
        if (found) {
          setAgentResult(found);
          setAgentRunning(false);
          setRunningAlertId(null);
        } else {
          setTimeout(checkResult, 1000);
        }
      };
      setTimeout(checkResult, 2000);
      setTimeout(() => {
        setAgentRunning(false);
        setRunningAlertId(null);
      }, 60000);
    } catch (e) {
      setAgentRunning(false);
      setRunningAlertId(null);
    }
  };

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Epidemic Radar" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm mb-6">
          <h3 className="font-semibold text-gray-800 mb-1">
            Inject IDSP Test Alert
          </h3>
          <p className="text-xs text-gray-400 mb-4">
            Simulates an IDSP disease surveillance bulletin being received
          </p>
          <div className="flex gap-3 flex-wrap items-end">
            <div>
              <label className="text-xs text-gray-500 block mb-1">City</label>
              <select
                value={injectCity}
                onChange={(e) => setInjectCity(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {CITIES.map((c) => (
                  <option key={c}>{c}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">Disease</label>
              <select
                value={injectDisease}
                onChange={(e) => setInjectDisease(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {DISEASES.map((d) => (
                  <option key={d}>{d}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">
                Alert Level
              </label>
              <select
                value={injectLevel}
                onChange={(e) => setInjectLevel(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                {ALERT_LEVELS.map((l) => (
                  <option key={l}>{l}</option>
                ))}
              </select>
            </div>
            <button
              onClick={injectAlert}
              className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-all shadow-sm"
            >
              <PlusCircle size={14} />
              Inject Alert
            </button>
            <button
              onClick={refresh}
              className="px-3 py-2 bg-white border border-gray-200 rounded-lg text-gray-500 hover:bg-gray-50"
            >
              <RefreshCw size={14} />
            </button>
          </div>
        </div>

        <div className="mb-2 flex items-center justify-between">
          <h3 className="font-semibold text-gray-700">
            Active IDSP Alerts ({alerts.length})
          </h3>
          <p className="text-xs text-gray-400">
            Auto-updates every 60 seconds
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {alerts.length === 0 && (
            <div className="md:col-span-2 bg-white rounded-xl p-10 border border-gray-200 text-center text-gray-400">
              <Activity size={32} className="mx-auto mb-3 opacity-30" />
              <p>No active disease alerts</p>
              <p className="text-xs mt-1">
                Use the inject tool above to simulate an IDSP alert
              </p>
            </div>
          )}
          {alerts.map((alert) => (
            <div
              key={alert.alert_id || alert.id}
              className={
                'rounded-xl p-5 border shadow-sm ' +
                (LEVEL_STYLES[alert.alert_level] || 'bg-white border-gray-200')
              }
            >
              <div className="flex items-start justify-between mb-3">
                <div>
                  <h4 className="font-semibold text-gray-800 capitalize">
                    {alert.disease_name}
                  </h4>
                  <div className="flex items-center gap-1 text-sm text-gray-500 mt-0.5">
                    <MapPin size={12} />
                    {alert.district}, {alert.city}
                  </div>
                </div>
                <StatusBadge status={alert.alert_level} />
              </div>

              <div className="grid grid-cols-2 gap-3 mb-4">
                <div>
                  <p className="text-xs text-gray-500">Cases Reported</p>
                  <p className="text-2xl font-bold text-gray-800">
                    {alert.case_count?.toLocaleString()}
                  </p>
                </div>
                <div>
                  <p className="text-xs text-gray-500">IDSP Bulletin</p>
                  <p className="text-xs font-mono text-gray-600 break-all mt-0.5">
                    {alert.idsp_bulletin_id}
                  </p>
                </div>
              </div>

              <div className="flex items-center justify-between">
                <p className="text-xs text-gray-400">
                  Reported:{' '}
                  {new Date(alert.reported_date).toLocaleDateString()}
                </p>
                <button
                  onClick={() => runPULSE(alert)}
                  disabled={agentRunning}
                  className="flex items-center gap-1.5 px-3 py-1.5 bg-emerald-600 text-white rounded-lg text-xs font-medium hover:bg-emerald-700 disabled:opacity-50 transition-all"
                >
                  <Play size={11} />
                  {runningAlertId === alert.alert_id
                    ? 'Running...'
                    : 'Run PULSE'}
                </button>
              </div>
            </div>
          ))}
        </div>

        {agentRunning && (
          <div className="bg-blue-50 rounded-lg p-4 flex items-center gap-3 mb-4 border border-blue-200">
            <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full shrink-0" />
            <div>
              <p className="text-sm font-medium text-blue-700">
                PULSE generating epidemic forecast...
              </p>
              <p className="text-xs text-blue-500 mt-0.5">
                PULSE analysis → PULSE critique → Planner synthesis → Planner
                critique
              </p>
            </div>
          </div>
        )}

        {agentResult?.pulse_decision && (
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <h3 className="font-semibold text-gray-800 mb-4">
              PULSE Epidemic Forecast Results
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-5">
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">Risk Level</p>
                <StatusBadge
                  status={
                    agentResult.pulse_decision.epidemic_risk_level || 'ALERT'
                  }
                  size="base"
                />
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">Revenue Protected</p>
                <p className="text-xl font-bold text-gray-800 mt-0.5">
                  Rs{' '}
                  {(
                    (agentResult.pulse_decision
                      .revenue_protection_opportunity_inr || 0) / 100000
                  ).toFixed(1)}
                  L
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500 mb-1">PULSE Critique</p>
                <StatusBadge
                  status={agentResult.pulse_critique_verdict || 'APPROVED'}
                  size="base"
                />
              </div>
              <div className="bg-gray-50 rounded-lg p-3">
                <p className="text-xs text-gray-500">SOMA Footfall Mult.</p>
                <p className="text-xl font-bold text-gray-800 mt-0.5">
                  {agentResult.pulse_decision.footfall_multiplier_for_soma ||
                    '—'}
                  x
                </p>
              </div>
            </div>

            {(agentResult.pulse_decision.sku_forecasts || []).length > 0 && (
              <div>
                <p className="text-sm font-semibold text-gray-700 mb-2">
                  SKU Demand Forecasts
                </p>
                <div className="space-y-2">
                  {agentResult.pulse_decision.sku_forecasts
                    .slice(0, 6)
                    .map((sku, i) => (
                      <div
                        key={i}
                        className="flex items-center justify-between bg-gray-50 rounded-lg px-4 py-3"
                      >
                        <div>
                          <p className="text-sm font-medium text-gray-700">
                            {sku.drug_name}
                          </p>
                          <p className="text-xs text-gray-400">
                            Baseline: {sku.baseline_daily_demand}/day →
                            Forecast: {sku.forecasted_daily_demand}/day
                          </p>
                        </div>
                        <div className="text-right">
                          <span className="text-sm font-bold text-amber-600">
                            {sku.demand_multiplier}x
                          </span>
                          {sku.days_until_stockout_current_inventory !==
                            undefined && (
                            <p className="text-xs text-gray-400">
                              {sku.days_until_stockout_current_inventory}d to
                              stockout
                            </p>
                          )}
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            )}

            {agentResult.store_communication && (
              <div className="mt-4 bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-1.5">
                  Store Operations Communication
                </p>
                <p className="text-sm text-emerald-800 leading-relaxed">
                  {agentResult.store_communication}
                </p>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}