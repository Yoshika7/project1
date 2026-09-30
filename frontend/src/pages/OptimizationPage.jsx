import React, { useState } from 'react';
import { Cpu, Play, Square } from 'lucide-react';
import { startOptimization } from '../services/api';
import { useOptimizationPoller } from '../hooks/useOptimization';
import MetricsDisplay from '../components/MetricsDisplay';
import FuzzyDiagnostic from '../components/FuzzyDiagnostic';
import NetworkGraph from '../components/NetworkGraph';
import { FitnessChart, AdaptiveParamsChart } from '../components/OptimizationCharts';

export default function OptimizationPage({ scenario, runId, setRunId }) {
  const [isAdaptive, setIsAdaptive] = useState(true);
  const [generations, setGenerations] = useState(100);
  const [popSize, setPopSize] = useState(80);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const { status } = useOptimizationPoller(runId, 700);

  const handleStart = async () => {
    if (!scenario) { setError('Generate a scenario first.'); return; }
    setLoading(true);
    setError(null);
    try {
      const res = await startOptimization({
        scenario_id: scenario.id,
        is_adaptive: isAdaptive,
        generations,
        population_size: popSize,
        seed: scenario.seed,
      });
      setRunId(res.run_id);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const history = status?.history || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <Cpu size={22} color="#06b6d4" />
          <div>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Optimization</h1>
            <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Run Baseline GA or Fuzzy-Adaptive AdaptIQ-R</p>
          </div>
        </div>
        {runId && (
          <div style={{ fontSize: 12, color: '#475569', fontFamily: 'monospace' }}>Run: {runId}</div>
        )}
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Left: Config + Metrics */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div className="card-header">
              <div className="card-title">Algorithm</div>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
              {[true, false].map((adaptive) => (
                <button
                  key={String(adaptive)}
                  onClick={() => setIsAdaptive(adaptive)}
                  style={{
                    padding: '0.65rem', borderRadius: 8, fontSize: 12, fontWeight: 700, cursor: 'pointer',
                    border: `1px solid ${isAdaptive === adaptive ? '#06b6d4' : '#334155'}`,
                    background: isAdaptive === adaptive ? 'rgba(6,182,212,0.1)' : '#1e293b',
                    color: isAdaptive === adaptive ? '#06b6d4' : '#94a3b8',
                  }}
                >
                  {adaptive ? 'AdaptIQ-R' : 'Baseline GA'}
                </button>
              ))}
            </div>

            <div style={{ marginBottom: '0.75rem' }}>
              <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Generations: {generations}</label>
              <input type="range" min={20} max={300} value={generations}
                onChange={(e) => setGenerations(Number(e.target.value))}
                style={{ width: '100%', marginTop: 4, accentColor: '#06b6d4' }} />
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Population: {popSize}</label>
              <input type="range" min={20} max={200} step={10} value={popSize}
                onChange={(e) => setPopSize(Number(e.target.value))}
                style={{ width: '100%', marginTop: 4, accentColor: '#10b981' }} />
            </div>

            <button onClick={handleStart} disabled={loading || status?.status === 'running'} className="btn btn-emerald" style={{ width: '100%' }}>
              <Play size={14} />
              {loading ? 'Starting…' : status?.status === 'running' ? 'Running…' : 'Start'}
            </button>

            {error && <div style={{ marginTop: '0.5rem', fontSize: 12, color: '#ef4444', padding: '0.4rem', background: 'rgba(239,68,68,0.1)', borderRadius: 6 }}>{error}</div>}
          </div>

          <div className="card">
            <MetricsDisplay status={status} scenario={scenario} />
          </div>
        </div>

        {/* Right: Charts + Network */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Fitness Chart */}
          <div className="card">
            <div className="card-header">
              <div className="card-title">Fitness Convergence</div>
              <span style={{ fontSize: 11, color: '#475569' }}>{history.length} generations</span>
            </div>
            <FitnessChart history={history} />
          </div>

          {/* Adaptive Params Chart */}
          {isAdaptive && (
            <div className="card">
              <div className="card-header">
                <div className="card-title">Fuzzy Adaptive Parameters</div>
              </div>
              <AdaptiveParamsChart history={history} />
            </div>
          )}

          {/* Network */}
          <div className="card" style={{ padding: 0 }}>
            <div style={{ padding: '0.75rem 1.25rem', borderBottom: '1px solid #1e293b', display: 'flex', justifyContent: 'space-between' }}>
              <span style={{ fontSize: 14, fontWeight: 600, color: '#f8fafc' }}>Network & Current Route</span>
              {status?.is_feasible !== undefined && (
                <span style={{ fontSize: 11, color: status.is_feasible ? '#10b981' : '#ef4444', fontWeight: 700 }}>
                  {status.is_feasible ? '✓ FEASIBLE' : '✗ INFEASIBLE'}
                </span>
              )}
            </div>
            <NetworkGraph
              scenario={scenario}
              currentRoute={status?.best_route || []}
              detailedPath={status?.detailed_path || []}
              height={380}
            />
          </div>
        </div>
      </div>

      {/* Fuzzy Diagnostic Section */}
      {isAdaptive && (
        <div>
          <h2 style={{ fontSize: '1rem', fontWeight: 700, color: '#94a3b8', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            Fuzzy Controller Diagnostics
          </h2>
          <FuzzyDiagnostic status={status} />
        </div>
      )}
    </div>
  );
}
