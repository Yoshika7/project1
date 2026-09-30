import { useState, useEffect, useRef, useCallback } from 'react';
import { getOptimizationStatus } from '../services/api';

/**
 * Custom hook that polls the optimization status endpoint while a run is active.
 * Returns live state that drives all real-time UI panels.
 */
export function useOptimizationPoller(runId, intervalMs = 600) {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const timerRef = useRef(null);

  const fetchStatus = useCallback(async () => {
    if (!runId) return;
    try {
      const data = await getOptimizationStatus(runId);
      setStatus(data);
      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    } catch (err) {
      setError(err.message);
    }
  }, [runId]);

  useEffect(() => {
    if (!runId) return;
    fetchStatus();
    timerRef.current = setInterval(fetchStatus, intervalMs);
    return () => clearInterval(timerRef.current);
  }, [runId, fetchStatus, intervalMs]);

  return { status, error };
}
