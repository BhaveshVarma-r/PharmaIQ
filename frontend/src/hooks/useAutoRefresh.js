import { useState, useEffect, useCallback, useRef } from 'react';
import { wsClient } from '../services/websocket';

export function useAutoRefresh(fetchFn, intervalMs = 60000, wsRefreshOn = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);
  const fetchRef = useRef(fetchFn);
  fetchRef.current = fetchFn;

  const refresh = useCallback(async () => {
    try {
      const result = await fetchRef.current();
      const payload = result && result.data !== undefined ? result.data : result;
      setData(payload);
      setError(null);
      setLastRefresh(new Date());
    } catch (e) {
      setError(e.message || 'Fetch failed');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    if (intervalMs <= 0) return;
    const timer = setInterval(refresh, intervalMs);
    return () => clearInterval(timer);
  }, [refresh, intervalMs]);

  useEffect(() => {
    if (wsRefreshOn.length === 0) return;
    const unsubscribers = wsRefreshOn.map((eventType) =>
      wsClient.on(eventType, () => refresh())
    );
    return () => unsubscribers.forEach((off) => off());
  }, [wsRefreshOn.join(','), refresh]);

  return { data, loading, error, refresh, lastRefresh };
}