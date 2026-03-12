import { useState, useCallback } from 'react';
import { coldChainAPI, agentAPI } from '../services/api';
import { usePharmaStore } from '../store/pharmaStore';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import StatusBadge from '../components/shared/StatusBadge';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
  ResponsiveContainer,
} from 'recharts';
import {
  Thermometer,
  AlertTriangle,
  Play,
  RefreshCw,
  CheckCircle,
} from 'lucide-react';

const STORES_SAMPLE = [
  'MC0001', 'MC0002', 'MC0003', 'MC0004', 'MC0005',
  'MC0006', 'MC0007', 'MC0008',
];

export default function ColdChainPage() {
  const [selectedStore, setSelectedStore] = useState('MC0001');
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentResult, setAgentResult] = useState(null);
  const [forceBreach, setForceBreach] = useState('power_fluctuation');
  const { sensorReadings } = usePharmaStore();

  const fetchStoreData = useCallback(
    () => coldChainAPI.getStoreDetail(selectedStore),
    [selectedStore]
  );

  const { data: storeData, loading, refresh } = useAutoRefresh(
    fetchStoreData,
    30000,
    ['sensor_reading', 'breach_alert']
  );

  const runSOMAColdChain = async () => {
    setAgentRunning(true);
    setAgentResult(null);
    try {
      const r = await agentAPI.runEvent({
        event_type: 'cold_chain_breach',
        store_id: selectedStore,
        force_breach: forceBreach,
      });
      const checkResult = () => {
        const results = usePharmaStore.getState().agentResults;
        const found = Object.values(results).find((v) => v && v.event_type === 'cold_chain_breach');
        if (found) {
          setAgentResult(found);
          setAgentRunning(false);
        } else {
          setTimeout(checkResult, 1000);
        }
      };
      setTimeout(checkResult, 2000);
      setTimeout(() => setAgentRunning(false), 60000);
    } catch (e) {
      setAgentRunning(false);
    }
  };

  const tempData = (storeData?.fridges?.[0]?.history || [])
    .slice(0, 30)
    .reverse()
    .map((r) => ({
      time: new Date(r.timestamp).toLocaleTimeString('en-IN', {
        hour: '2-digit',
        minute: '2-digit',
      }),
      temp: r.temperature,
    }));

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Cold Chain Monitor" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">

        <div className="flex gap-2 mb-6 flex-wrap items-center">
          {STORES_SAMPLE.map((sid) => (
            <button
              key={sid}
              onClick={() => setSelectedStore(sid)}
              className={
                'px-4 py-2 rounded-lg text-sm font-medium transition-all ' +
                (selectedStore === sid
                  ? 'bg-emerald-600 text-white shadow-md'
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-emerald-300 hover:text-emerald-600')
              }
            >
              {sid}
            </button>
          ))}
          <button
            onClick={refresh}
            className="px-3 py-2 rounded-lg bg-white border border-gray-200 hover:bg-gray-50 text-gray-500"
          >
            <RefreshCw size={15} className={loading ? 'animate-spin' : ''} />
          </button>
        </div>

        {loading && !storeData ? (
          <div className="flex items-center justify-center py-20">
            <div className="animate-spin w-8 h-8 border-4 border-emerald-500 border-t-transparent rounded-full" />
          </div>
        ) : (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 mb-6">
            <div className="xl:col-span-1 space-y-4">
              <h3 className="font-semibold text-gray-700 text-sm uppercase tracking-wide">
                Refrigeration Units — {selectedStore}
              </h3>
              {(storeData?.fridges || []).map((fridge) => {
                const liveKey = selectedStore + '_' + fridge.fridge_id;
                const liveReading = sensorReadings[liveKey];
                const reading = liveReading || fridge.latest_reading || {};
                const temp = reading.temperature;
                const isBreach = temp !== undefined && (temp > 8 || temp < 2);
                return (
                  <div
                    key={fridge.fridge_id}
                    className={
                      'bg-white rounded-xl p-4 border shadow-sm transition-all ' +
                      (isBreach
                        ? 'border-red-300 bg-red-50'
                        : 'border-gray-200')
                    }
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="font-medium text-sm text-gray-700">
                        {fridge.fridge_id}
                      </span>
                      <StatusBadge status={isBreach ? 'BREACH' : 'NORMAL'} />
                    </div>
                    <div className="flex items-end gap-2">
                      <Thermometer
                        size={20}
                        className={
                          isBreach ? 'text-red-500' : 'text-emerald-500'
                        }
                      />
                      <span
                        className={
                          'text-3xl font-bold ' +
                          (isBreach ? 'text-red-600' : 'text-gray-800')
                        }
                      >
                        {temp !== undefined ? temp.toFixed(1) : '--'}
                        {'\u00b0'}C
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-gray-400 space-y-0.5">
                      <div>
                        Humidity: {reading.humidity?.toFixed(0) || '--'}%
                      </div>
                      <div>
                        Battery: {reading.battery_level?.toFixed(0) || '--'}%
                      </div>
                      {liveReading && (
                        <div className="text-emerald-500 font-medium">
                          Live
                        </div>
                      )}
                    </div>
                    {isBreach && (
                      <div className="mt-2 flex items-center gap-1 text-xs text-red-600 font-medium">
                        <AlertTriangle size={12} />
                        {reading.breach_type || 'Temperature breach'}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>

            <div className="xl:col-span-2 bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
              <h3 className="font-semibold text-gray-700 mb-1">
                Temperature History
              </h3>
              <p className="text-xs text-gray-400 mb-4">
                Safe range: 2{'\u00b0'}C to 8{'\u00b0'}C (WHO cold chain protocol)
              </p>
              {tempData.length > 0 ? (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={tempData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis
                      dataKey="time"
                      tick={{ fontSize: 10 }}
                      interval="preserveStartEnd"
                    />
                    <YAxis
                      domain={[0, 14]}
                      tick={{ fontSize: 10 }}
                      tickFormatter={(v) => v + '\u00b0'}
                    />
                    <Tooltip
                      formatter={(v) => [v.toFixed(1) + '\u00b0C', 'Temp']}
                    />
                    <ReferenceLine
                      y={8}
                      stroke="#ef4444"
                      strokeDasharray="5 5"
                      label={{ value: '8\u00b0C max', fontSize: 10, fill: '#ef4444' }}
                    />
                    <ReferenceLine
                      y={2}
                      stroke="#3b82f6"
                      strokeDasharray="5 5"
                      label={{ value: '2\u00b0C min', fontSize: 10, fill: '#3b82f6' }}
                    />
                    <Line
                      type="monotone"
                      dataKey="temp"
                      stroke="#10b981"
                      strokeWidth={2}
                      dot={false}
                      activeDot={{ r: 4 }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              ) : (
                <div className="h-64 flex items-center justify-center text-gray-400">
                  No temperature history available
                </div>
              )}
            </div>
          </div>
        )}

        <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
          <div className="flex items-start justify-between mb-4">
            <div>
              <h3 className="font-semibold text-gray-800">
                Run SOMA Cold Chain Analysis
              </h3>
              <p className="text-sm text-gray-500 mt-1">
                Triggers full pipeline: SOMA analysis, SOMA critique, PULSE
                coordination, Planner synthesis, Planner critique
              </p>
            </div>
          </div>

          <div className="flex gap-3 flex-wrap mb-4">
            {[
              {
                value: 'power_fluctuation',
                label: 'Power Fluctuation (Moderate)',
                color: 'amber',
              },
              {
                value: 'door_left_open',
                label: 'Door Left Open (Moderate)',
                color: 'orange',
              },
              {
                value: 'compressor_fault',
                label: 'Compressor Fault (Critical)',
                color: 'red',
              },
            ].map((scenario) => (
              <button
                key={scenario.value}
                onClick={() => setForceBreach(scenario.value)}
                className={
                  'px-3 py-2 rounded-lg text-sm font-medium border transition-all ' +
                  (forceBreach === scenario.value
                    ? 'bg-emerald-600 text-white border-emerald-600'
                    : 'bg-white text-gray-600 border-gray-200 hover:border-gray-300')
                }
              >
                {scenario.label}
              </button>
            ))}
          </div>

          <button
            onClick={runSOMAColdChain}
            disabled={agentRunning}
            className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-all shadow-sm"
          >
            <Play size={14} />
            {agentRunning ? 'Running agent pipeline...' : 'Run SOMA Analysis'}
          </button>

          {agentRunning && (
            <div className="mt-4 bg-blue-50 rounded-lg p-4 flex items-center gap-3">
              <div className="animate-spin w-5 h-5 border-2 border-blue-500 border-t-transparent rounded-full shrink-0" />
              <div>
                <p className="text-sm font-medium text-blue-700">
                  Agent pipeline running...
                </p>
                <p className="text-xs text-blue-500 mt-0.5">
                  Planner decompose → SOMA → SOMA critique → PULSE → PULSE
                  critique → Planner synthesis → Planner critique
                </p>
              </div>
            </div>
          )}

          {agentResult && (
            <div className="mt-4 space-y-4">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">SOMA Critique</p>
                  <StatusBadge
                    status={agentResult.soma_critique_verdict || 'APPROVED'}
                    size="base"
                  />
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">PULSE Critique</p>
                  <StatusBadge
                    status={agentResult.pulse_critique_verdict || 'APPROVED'}
                    size="base"
                  />
                </div>
                <div className="bg-gray-50 rounded-lg p-3">
                  <p className="text-xs text-gray-500 mb-1">Planner Critique</p>
                  <StatusBadge
                    status={
                      agentResult.planner_critique_verdict || 'APPROVED'
                    }
                    size="base"
                  />
                </div>
              </div>

              {agentResult.store_communication && (
                <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4">
                  <p className="text-xs font-semibold text-emerald-700 uppercase tracking-wide mb-1.5">
                    Store Operations Communication
                  </p>
                  <p className="text-sm text-emerald-800 leading-relaxed">
                    {agentResult.store_communication}
                  </p>
                </div>
              )}

              {(agentResult.integrated_action_plan || []).length > 0 && (
                <div>
                  <p className="text-sm font-semibold text-gray-700 mb-2">
                    Integrated Action Plan
                  </p>
                  <div className="space-y-2">
                    {agentResult.integrated_action_plan
                      .slice(0, 6)
                      .map((action, i) => (
                        <div
                          key={i}
                          className="flex items-start gap-3 bg-gray-50 rounded-lg px-4 py-3"
                        >
                          <span className="text-xs font-bold text-gray-400 mt-0.5 w-5 shrink-0">
                            #{action.sequence || i + 1}
                          </span>
                          <div className="flex-1">
                            <p className="text-sm text-gray-700">
                              {action.action}
                            </p>
                            <div className="flex gap-2 mt-1 flex-wrap">
                              <span className="text-xs text-gray-400">
                                {action.responsible_system}
                              </span>
                              {action.requires_human_approval && (
                                <span className="text-xs bg-amber-100 text-amber-700 px-2 py-0.5 rounded-full">
                                  Human Approval Required
                                </span>
                              )}
                              {action.deadline_minutes && (
                                <span className="text-xs text-gray-400">
                                  within {action.deadline_minutes} min
                                </span>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {agentResult.errors && agentResult.errors.length > 0 && (
                <div className="bg-red-50 rounded-lg p-3">
                  <p className="text-xs font-semibold text-red-700 mb-1">
                    Pipeline Errors
                  </p>
                  {agentResult.errors.map((e, i) => (
                    <p key={i} className="text-xs text-red-600">
                      {e}
                    </p>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}