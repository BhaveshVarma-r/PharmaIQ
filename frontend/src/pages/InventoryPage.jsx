import { useState, useCallback } from 'react';
import { inventoryAPI } from '../services/api';
import { useAutoRefresh } from '../hooks/useAutoRefresh';
import Header from '../components/shared/Header';
import StatusBadge from '../components/shared/StatusBadge';
import { Package, AlertTriangle, RefreshCw, TrendingDown } from 'lucide-react';

export default function InventoryPage() {
  const [daysFilter, setDaysFilter] = useState(60);
  const [selectedStore, setSelectedStore] = useState('');

  const fetchNearExpiry = useCallback(
    () => inventoryAPI.getNearExpiry(daysFilter, selectedStore || undefined),
    [daysFilter, selectedStore]
  );

  const { data: expiryData, loading, refresh } = useAutoRefresh(
    fetchNearExpiry,
    60000,
    ['expiry_alert', 'inventory_update']
  );

  const items = expiryData?.items || [];

  const getTierColor = (days) => {
    if (days <= 30) return 'bg-red-50 border-red-200 text-red-800';
    if (days <= 45) return 'bg-orange-50 border-orange-200 text-orange-800';
    return 'bg-amber-50 border-amber-200 text-amber-800';
  };

  const getTier = (item) => {
    const days = Math.floor(
      (new Date(item.expiry_date) - new Date()) / (1000 * 60 * 60 * 24)
    );
    const stock = item.quantity / (item.avg_daily_velocity || 1);
    if (days <= 30 && stock > 60) return 'TIER1';
    if (days <= 45 && stock > 45) return 'TIER2';
    return 'TIER3';
  };

  const totalValue = expiryData?.total_value_inr || 0;

  return (
    <div className="flex-1 flex flex-col overflow-hidden">
      <Header title="Near-Expiry Inventory" />
      <div className="flex-1 overflow-auto p-6 bg-gray-50">

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <p className="text-sm text-gray-500">Total Near-Expiry Items</p>
            <p className="text-3xl font-bold text-gray-900 mt-1">
              {(expiryData?.count || 0).toLocaleString()}
            </p>
            <p className="text-xs text-gray-400 mt-1">
              Within {daysFilter} days
            </p>
          </div>
          <div className="bg-white rounded-xl p-5 border border-red-200 shadow-sm">
            <p className="text-sm text-gray-500">At-Risk Value</p>
            <p className="text-3xl font-bold text-red-600 mt-1">
              Rs {(totalValue / 100000).toFixed(1)}L
            </p>
            <p className="text-xs text-gray-400 mt-1">Potential write-off</p>
          </div>
          <div className="bg-white rounded-xl p-5 border border-gray-200 shadow-sm">
            <p className="text-sm text-gray-500">Critical Items (30 days)</p>
            <p className="text-3xl font-bold text-orange-600 mt-1">
              {items.filter((i) => {
                const d = Math.floor(
                  (new Date(i.expiry_date) - new Date()) /
                    (1000 * 60 * 60 * 24)
                );
                return d <= 30;
              }).length}
            </p>
            <p className="text-xs text-gray-400 mt-1">Immediate action needed</p>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm mb-6 p-4">
          <div className="flex gap-3 flex-wrap items-center">
            <div>
              <label className="text-xs text-gray-500 block mb-1">
                Days Threshold
              </label>
              <select
                value={daysFilter}
                onChange={(e) => setDaysFilter(Number(e.target.value))}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm bg-white focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value={30}>30 days</option>
                <option value={45}>45 days</option>
                <option value={60}>60 days</option>
                <option value={90}>90 days</option>
              </select>
            </div>
            <div>
              <label className="text-xs text-gray-500 block mb-1">
                Store Filter
              </label>
              <input
                type="text"
                placeholder="e.g. MC0001"
                value={selectedStore}
                onChange={(e) => setSelectedStore(e.target.value)}
                className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
            <div className="mt-4">
              <button
                onClick={refresh}
                className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-600 hover:bg-gray-50"
              >
                <RefreshCw
                  size={14}
                  className={loading ? 'animate-spin' : ''}
                />
                Refresh
              </button>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-5 py-4 border-b border-gray-100 flex items-center justify-between">
            <h3 className="font-semibold text-gray-800">Near-Expiry Items</h3>
            <p className="text-xs text-gray-400">
              Auto-refreshes every 60s
            </p>
          </div>

          {loading && items.length === 0 ? (
            <div className="p-8 flex justify-center">
              <div className="animate-spin w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full" />
            </div>
          ) : items.length === 0 ? (
            <div className="p-10 text-center text-gray-400">
              <Package size={32} className="mx-auto mb-3 opacity-30" />
              <p>No near-expiry items found</p>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50 border-b border-gray-100">
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Drug
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Store
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Expiry
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Qty
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Days Left
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Risk
                    </th>
                    <th className="text-left px-5 py-3 text-xs font-semibold text-gray-500 uppercase tracking-wide">
                      Value
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-50">
                  {items.slice(0, 50).map((item, i) => {
                    const daysLeft = Math.floor(
                      (new Date(item.expiry_date) - new Date()) /
                        (1000 * 60 * 60 * 24)
                    );
                    const tier = getTier(item);
                    const value = (item.cost_price || 0) * item.quantity;
                    return (
                      <tr
                        key={i}
                        className="hover:bg-gray-50 transition-colors"
                      >
                        <td className="px-5 py-3">
                          <p className="text-sm font-medium text-gray-700">
                            {item.drug_name}
                          </p>
                          <p className="text-xs text-gray-400">
                            {item.schedule_type} ·{' '}
                            {item.is_cold_chain ? 'Cold Chain' : 'Ambient'}
                          </p>
                        </td>
                        <td className="px-5 py-3 text-sm text-gray-600">
                          {item.store_id}
                          <br />
                          <span className="text-xs text-gray-400">
                            {item.city}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-sm text-gray-600">
                          {new Date(item.expiry_date).toLocaleDateString()}
                        </td>
                        <td className="px-5 py-3 text-sm text-gray-600">
                          {item.quantity.toLocaleString()}
                        </td>
                        <td className="px-5 py-3">
                          <span
                            className={
                              'text-sm font-bold ' +
                              (daysLeft <= 30
                                ? 'text-red-600'
                                : daysLeft <= 45
                                ? 'text-orange-600'
                                : 'text-amber-600')
                            }
                          >
                            {daysLeft}d
                          </span>
                        </td>
                        <td className="px-5 py-3">
                          <span
                            className={
                              'text-xs font-medium px-2 py-0.5 rounded-full border ' +
                              getTierColor(daysLeft)
                            }
                          >
                            {tier}
                          </span>
                        </td>
                        <td className="px-5 py-3 text-sm text-gray-600">
                          Rs {value.toLocaleString()}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
              {items.length > 50 && (
                <div className="px-5 py-3 text-xs text-gray-400 text-center border-t border-gray-100">
                  Showing 50 of {items.length} items
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}