import React from 'react';
import { BarChart3, Info, ShieldAlert, Cpu } from 'lucide-react';
import { useOptimizationPoller } from '../hooks/useOptimization';
import { FitnessChart, AdaptiveParamsChart } from '../components/OptimizationCharts';

export default function AnalyticsPage({ runId }) {
  const { status } = useOptimizationPoller(runId, 1000);
  const history = status?.history || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <BarChart3 size={22} color="#06b6d4" />
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Research Analytics</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Deep algorithmic telemetry, diversity decay curves, and parameter response analysis</p>
        </div>
      </div>

      {!runId && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem 1rem' }}>
          <p style={{ color: '#64748b', margin: 0 }}>No active or completed run loaded. Start an optimization from the <strong>Optimize</strong> page first.</p>
        </div>
      )}

      {runId && (
        <>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
            <div className="card">
              <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Total Generations</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#f8fafc', fontFamily: 'monospace', marginTop: 4 }}>
                {history.length}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Terminal Diversity</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#10b981', fontFamily: 'monospace', marginTop: 4 }}>
                {status?.diversity?.toFixed(4) || '—'}
              </div>
            </div>
            <div className="card">
              <div style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Mean Mutation Level</div>
              <div style={{ fontSize: 24, fontWeight: 800, color: '#f59e0b', fontFamily: 'monospace', marginTop: 4 }}>
                {history.length > 0 ? (history.reduce((a, b) => a + (b.mutation_rate || 0), 0) / history.length).toFixed(4) : '—'}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Convergence Profile</div>
            </div>
            <FitnessChart history={history} />
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Adaptive Feedback Dynamics</div>
            </div>
            <AdaptiveParamsChart history={history} />
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-title">Generational Telemetry Log (Sampled)</div>
            </div>
            <div style={{ maxHeight: 250, overflowY: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid #1e293b', color: '#64748b', textAlign: 'left' }}>
                    <th style={{ padding: '6px 8px' }}>Gen</th>
                    <th style={{ padding: '6px 8px' }}>Best Fit</th>
                    <th style={{ padding: '6px 8px' }}>Avg Fit</th>
                    <th style={{ padding: '6px 8px' }}>Diversity</th>
                    <th style={{ padding: '6px 8px' }}>Mutation</th>
                    <th style={{ padding: '6px 8px' }}>Exploration</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(-20).map((m) => (
                    <tr key={m.generation} style={{ borderBottom: '1px solid #1e293b', fontFamily: 'monospace' }}>
                      <td style={{ padding: '6px 8px', color: '#94a3b8' }}>{m.generation}</td>
                      <td style={{ padding: '6px 8px', color: '#06b6d4' }}>{m.best_fitness?.toFixed(4)}</td>
                      <td style={{ padding: '6px 8px', color: '#64748b' }}>{m.avg_fitness?.toFixed(4)}</td>
                      <td style={{ padding: '6px 8px', color: '#10b981' }}>{m.population_diversity?.toFixed(4)}</td>
                      <td style={{ padding: '6px 8px', color: '#f59e0b' }}>{m.mutation_rate?.toFixed(4)}</td>
                      <td style={{ padding: '6px 8px', color: '#8b5cf6' }}>{m.exploration_level?.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
