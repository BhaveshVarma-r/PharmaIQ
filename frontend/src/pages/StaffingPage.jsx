import { useState, useCallback } from 'react';
import { staffAPI, agentAPI } from '../services/api';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import StatusBadge from '../components/shared/StatusBadge';
import { Users, AlertTriangle, Play, RefreshCw, Clock } from 'lucide-react';
import { usePharmaStore } from '../store/pharmaStore';

const STORES_SAMPLE = ['MC0001', 'MC0002', 'MC0003', 'MC0004', 'MC0005'];

export default function StaffingPage() {
  const [selectedStore, setSelectedStore] = useState('MC0001');
  const [agentRunning, setAgentRunning] = useState(false);
  const [agentResult, setAgentResult] = useState(null);

  const fetchSchedule = useCallback(
    () => staffAPI.getSchedule(selectedStore),
    [selectedStore]
  );

  const { data: scheduleData, loading, refresh } = useAutoRefresh(
    fetchSchedule,
    60000,
    []
  );

  const runSOMAStaffing = async () => {
    setAgentRunning(true);
    setAgentResult(null);
    try {
      await agentAPI.runEvent({
        event_type: 'staffing_check',
        store_id: selectedStore,
      });
      const checkResult = () => {
        const results = usePharmaStore.getState().agentResults;
        const found = Object.values(results).find(
          (v) => v && v.event_type === 'staffing_check'
        );
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

  const schedules = scheduleData?.schedules || [];
  const gaps = scheduleData?.compliance_gaps || [];

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Staff Scheduling" />
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
                  : 'bg-white text-gray-600 border border-gray-200 hover:border-emerald-300')
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

        {gaps.length > 0 && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 mb-6">
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={16} className="text-red-600" />
              <h3 className="font-semibold text-red-800">
                Schedule H Compliance Gaps Detected ({gaps.length})
              </h3>
            </div>
            <div className="space-y-2">
              {gaps.map((gap, i) => (
                <div
                  key={i}
                  className="flex items-center justify-between bg-white rounded-lg px-4 py-2.5 border border-red-100"
                >
                  <div className="flex items-center gap-2">
                    <Clock size={14} className="text-red-500" />
                    <span className="text-sm font-medium text-red-800">
                      {gap.time} — No registered pharmacist
                    </span>
                  </div>
                  <StatusBadge status={gap.severity} />
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
            <div className="px-5 py-4 border-b border-gray-100">
              <h3 className="font-semibold text-gray-800">
                Today's Schedule — {selectedStore}
              </h3>
              <p className="text-xs text-gray-400 mt-0.5">
                {scheduleData?.date || new Date().toLocaleDateString()}
              </p>
            </div>
            <div className="divide-y divide-gray-50">
              {loading ? (
                <div className="p-8 flex justify-center">
                  <div className="animate-spin w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full" />
                </div>
              ) : schedules.length === 0 ? (
                <div className="p-8 text-center text-gray-400 text-sm">
                  No schedules found for today
                </div>
              ) : (
                schedules.map((s, i) => (
                  <div key={i} className="px-5 py-3 flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-gray-700">
                        {s.staff_name}
                      </p>
                      <p className="text-xs text-gray-400">
                        {s.shift_start} - {s.shift_end} · {s.role}
                      </p>
                    </div>
                    <div className="flex items-center gap-2">
                      {s.is_registered_pharmacist === 1 && (
                        <span className="text-xs bg-emerald-100 text-emerald-700 px-2 py-0.5 rounded-full font-medium">
                          Reg. Pharmacist
                        </span>
                      )}
                      <StatusBadge status={s.status || 'scheduled'} />
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-5">
            <h3 className="font-semibold text-gray-800 mb-1">
              Run SOMA Staffing Analysis
            </h3>
            <p className="text-sm text-gray-500 mb-4">
              Analyse compliance gaps, optimise schedule, identify cost savings
            </p>

            <button
              onClick={runSOMAStaffing}
              disabled={agentRunning}
              className="flex items-center gap-2 px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-sm font-medium disabled:opacity-50 transition-all shadow-sm"
            >
              <Play size={14} />
              {agentRunning ? 'Running...' : 'Run SOMA Staffing Analysis'}
            </button>

            {agentRunning && (
              <div className="mt-4 bg-blue-50 rounded-lg p-3 flex items-center gap-2">
                <div className="animate-spin w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full shrink-0" />
                <p className="text-sm text-blue-700">
                  Analysing schedule compliance...
                </p>
              </div>
            )}

            {agentResult?.soma_decision && (
              <div className="mt-4 space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500 mb-1">SOMA Verdict</p>
                    <StatusBadge
                      status={agentResult.soma_critique_verdict || 'APPROVED'}
                      size="base"
                    />
                  </div>
                  <div className="bg-gray-50 rounded-lg p-3">
                    <p className="text-xs text-gray-500">Cost Savings</p>
                    <p className="text-lg font-bold text-gray-800">
                      Rs{' '}
                      {(
                        agentResult.soma_decision?.cost_impact
                          ?.estimated_overtime_savings_inr || 0
                      ).toLocaleString()}
                    </p>
                  </div>
                </div>

                {agentResult.soma_decision?.compliance_gaps?.length > 0 && (
                  <div>
                    <p className="text-xs font-semibold text-gray-600 mb-1">
                      Identified Compliance Gaps
                    </p>
                    {agentResult.soma_decision.compliance_gaps
                      .slice(0, 4)
                      .map((gap, i) => (
                        <div
                          key={i}
                          className="flex items-center justify-between text-xs bg-red-50 rounded px-3 py-2 mb-1"
                        >
                          <span className="text-red-700">
                            {gap.time_window || gap.time} — {gap.gap_type}
                          </span>
                          <StatusBadge status={gap.severity} />
                        </div>
                      ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}