import { useEffect, useState } from 'react';
import { Bell, Wifi, WifiOff, X } from 'lucide-react';
import { usePharmaStore } from '../../store/pharmaStore';
import { wsClient } from '../../services/websocket';

export default function Header({ title }) {
  const { liveAlerts, clearAlert } = usePharmaStore();
  const [connected, setConnected] = useState(false);
  const [showAlerts, setShowAlerts] = useState(false);

  useEffect(() => {
    const off1 = wsClient.on('connected', () => setConnected(true));
    const off2 = wsClient.on('disconnected', () => setConnected(false));
    return () => {
      off1();
      off2();
    };
  }, []);

  const criticalCount = liveAlerts.filter(
    (a) => a.type === 'breach_alert' || a.type === 'alert_escalated'
  ).length;

  return (
    <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 relative z-40">
      <h1 className="text-xl font-semibold text-gray-800">{title}</h1>

      <div className="flex items-center gap-4">
        {liveAlerts.length > 0 && (
          <div className="relative">
            <button
              onClick={() => setShowAlerts(!showAlerts)}
              className={
                'flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium transition-all ' +
                (criticalCount > 0
                  ? 'bg-red-50 text-red-700 hover:bg-red-100'
                  : 'bg-amber-50 text-amber-700 hover:bg-amber-100')
              }
            >
              <Bell size={14} />
              {liveAlerts.length} Alert{liveAlerts.length > 1 ? 's' : ''}
            </button>

            {showAlerts && (
              <div className="absolute right-0 top-10 w-96 bg-white border border-gray-200 rounded-xl shadow-2xl overflow-hidden">
                <div className="px-4 py-3 border-b border-gray-100 flex items-center justify-between">
                  <span className="font-semibold text-gray-800 text-sm">
                    Live Alerts
                  </span>
                  <button
                    onClick={() => setShowAlerts(false)}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X size={16} />
                  </button>
                </div>
                <div className="max-h-80 overflow-y-auto divide-y divide-gray-50">
                  {liveAlerts.slice(0, 15).map((alert) => (
                    <div
                      key={alert.id}
                      className="px-4 py-3 flex items-start justify-between hover:bg-gray-50"
                    >
                      <div className="flex-1 mr-2">
                        <p className="text-xs text-gray-700 leading-relaxed">
                          {alert.message}
                        </p>
                        <p className="text-xs text-gray-400 mt-0.5">
                          {alert.type}
                        </p>
                      </div>
                      <button
                        onClick={() => clearAlert(alert.id)}
                        className="text-gray-300 hover:text-gray-500 shrink-0"
                      >
                        <X size={12} />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        <div
          className={
            'flex items-center gap-1.5 text-sm ' +
            (connected ? 'text-emerald-600' : 'text-gray-400')
          }
        >
          {connected ? <Wifi size={15} /> : <WifiOff size={15} />}
          <span>{connected ? 'Live' : 'Reconnecting...'}</span>
        </div>
      </div>
    </header>
  );
}