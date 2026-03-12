import { useCallback } from 'react';
import { dashboardAPI } from '../services/api';
import { usePharmaStore } from '../store/pharmaStore';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import {
  Thermometer,
  Activity,
  AlertTriangle,
  Package,
  Clock,
  TrendingUp,
  RefreshCw,
  X,
} from 'lucide-react';

const TYPE_COLORS = {
  breach_alert: 'bg-red-50 border-red-200 text-red-800',
  low_stock_alert: 'bg-amber-50 border-amber-200 text-amber-800',
  new_disease_alert: 'bg-orange-50 border-orange-200 text-orange-800',
  alert_escalated: 'bg-red-50 border-red-200 text-red-800',
  order_delivered: 'bg-emerald-50 border-emerald-200 text-emerald-800',
  alert_resolved: 'bg-blue-50 border-blue-200 text-blue-800',
  expiry_alert: 'bg-purple-50 border-purple-200 text-purple-800',
};

function MetricCard({ title, value, sub, icon: Icon, color, pulse }) {
  const colors = {
    blue: 'bg-blue-50 text-blue-600',
    red: 'bg-red-50 text-red-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    purple: 'bg-purple-50 text-purple-600',
  };
  return (
    <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-gray-500 font-medium">{title}</p>
          <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
          {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
        </div>
        <div
          className={
            'p-3 rounded-xl shrink-0 ' +
            (colors[color] || colors.blue) +
            (pulse ? ' animate-pulse' : '')
          }
        >
          <Icon size={22} />
        </div>
      </div>
    </div>
  );
}

function AlertItem({ alert, onDismiss }) {
  const classes =
    TYPE_COLORS[alert.type] || 'bg-gray-50 border-gray-200 text-gray-800';
  return (
    <div
      className={
        'flex items-start justify-between rounded-lg px-4 py-3 border ' +
        classes
      }
    >
      <div className="flex items-start gap-2 flex-1">
        <AlertTriangle size={13} className="shrink-0 mt-0.5" />
        <span className="text-sm font-medium leading-snug">
          {alert.message}
        </span>
      </div>
      <button
        onClick={() => onDismiss(alert.id)}
        className="ml-3 opacity-50 hover:opacity-100 shrink-0"
      >
        <X size={13} />
      </button>
    </div>
  );
}

export default function DashboardPage() {
  const { liveAlerts, clearAlert, clearAllAlerts, liveStats } = usePharmaStore();

  const fetchSummary = useCallback(() => dashboardAPI.getSummary(), []);

  const { data: summary, loading, refresh, lastRefresh } = useAutoRefresh(
    fetchSummary,
    60000,
    ['inventory_update', 'disease_update', 'breach_alert', 'new_disease_alert']
  );

  if (loading || !summary) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="animate-spin w-10 h-10 border-4 border-emerald-500 border-t-transparent rounded-full mx-auto mb-3" />
          <p className="text-gray-500 text-sm">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  const totalBreaches = summary.cold_chain.breaches_24h + liveStats.breachCount;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Operations Dashboard" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        <div className="flex items-center justify-between mb-5">
          <div>
            <h2 className="text-lg font-semibold text-gray-800">
              MedChain India — Network Overview
            </h2>
            <p className="text-xs text-gray-400 mt-0.5">
              Auto-refreshes every 60 seconds. Sensor data every 15 seconds.
              {lastRefresh && (
                <span className="ml-1">
                  Last refresh: {lastRefresh.toLocaleTimeString()}
                </span>
              )}
            </p>
          </div>
          <button
            onClick={refresh}
            className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 px-3 py-2 rounded-lg hover:bg-white border border-transparent hover:border-gray-200 transition-all"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {liveAlerts.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm font-semibold text-gray-700">
                Live Alerts ({liveAlerts.length})
              </p>
              <button
                onClick={clearAllAlerts}
                className="text-xs text-gray-400 hover:text-gray-600 underline"
              >
                Clear all
              </button>
            </div>
            <div className="space-y-2">
              {liveAlerts.slice(0, 5).map((alert) => (
                <AlertItem key={alert.id} alert={alert} onDismiss={clearAlert} />
              ))}
              {liveAlerts.length > 5 && (
                <p className="text-xs text-gray-400 text-center">
                  +{liveAlerts.length - 5} more alerts
                </p>
              )}
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-5 mb-6">
          <MetricCard
            title="Total Stores"
            value={summary.stores.total.toLocaleString()}
            sub={summary.stores.tier1 + ' Tier 1  ' + summary.stores.tier2 + ' Tier 2'}
            icon={TrendingUp}
            color="blue"
          />
          <MetricCard
            title="Cold Chain Breaches (24h)"
            value={totalBreaches}
            sub={summary.cold_chain.total_fridges + ' fridges monitored'}
            icon={Thermometer}
            color={totalBreaches > 0 ? 'red' : 'emerald'}
            pulse={liveStats.breachCount > 0}
          />
          <MetricCard
            title="Active Disease Alerts"
            value={summary.disease_alerts.active}
            sub={summary.disease_alerts.cities_affected + ' cities affected'}
            icon={Activity}
            color={summary.disease_alerts.active > 0 ? 'amber' : 'emerald'}
          />
          <MetricCard
            title="Near-Expiry Items"
            value={summary.inventory.near_expiry_items.toLocaleString()}
            sub={
              'Rs ' +
              (summary.inventory.near_expiry_value_inr / 100000).toFixed(1) +
              'L at risk'
            }
            icon={Package}
            color="purple"
          />
          <MetricCard
            title="Agent Decisions (24h)"
            value={summary.agent_activity.decisions_24h}
            sub="Autonomous and supervised"
            icon={Clock}
            color="emerald"
          />
          <MetricCard
            title="Pending Approvals"
            value={summary.agent_activity.pending_approvals}
            sub="Awaiting human review"
            icon={AlertTriangle}
            color={
              summary.agent_activity.pending_approvals > 0 ? 'red' : 'emerald'
            }
            pulse={summary.agent_activity.pending_approvals > 0}
          />
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800">
              Recent System Activity
            </h3>
            <span className="text-xs text-gray-400">
              {new Date().toLocaleTimeString()}
            </span>
          </div>
          <div className="divide-y divide-gray-50">
            {(summary.recent_activity || []).map((item, i) => (
              <div key={i} className="px-5 py-3 flex items-start gap-3">
                <div className="w-2 h-2 rounded-full bg-emerald-400 mt-2 shrink-0" />
                <div className="flex-1">
                  <p className="text-sm text-gray-700">
                    {item.action_description}
                  </p>
                  <p className="text-xs text-gray-400 mt-0.5">
                    {new Date(item.timestamp).toLocaleString()} ·{' '}
                    {item.agent_name || 'system'}
                  </p>
                </div>
                <span className="text-xs bg-gray-100 text-gray-500 px-2 py-0.5 rounded shrink-0">
                  {item.event_type}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}