import React, { useState } from 'react';
import { GitCompare, Play, ArrowRight } from 'lucide-react';
import { startOptimization, getOptimizationStatus } from '../services/api';
import { FitnessChart, AdaptiveParamsChart } from '../components/OptimizationCharts';

export default function ComparisonPage({ scenario }) {
  const [generations, setGenerations] = useState(60);
  const [popSize, setPopSize] = useState(60);
  const [loading, setLoading] = useState(false);
  const [baselineData, setBaselineData] = useState(null);
  const [adaptiqData, setAdaptiqData] = useState(null);
  const [error, setError] = useState(null);

  const runSideBySide = async () => {
    if (!scenario) {
      setError('Please generate or select a scenario first.');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // 1. Run Baseline GA
      const bRes = await startOptimization({
        scenario_id: scenario.id,
        is_adaptive: false,
        generations,
        population_size: popSize,
        seed: scenario.seed
      });
      // 2. Run AdaptIQ-R
      const aRes = await startOptimization({
        scenario_id: scenario.id,
        is_adaptive: true,
        generations,
        population_size: popSize,
        seed: scenario.seed
      });

      // Poll both until completion
      const poll = async (runId) => {
        let attempts = 0;
        while (attempts < 120) {
          await new Promise(r => setTimeout(r, 600));
          const st = await getOptimizationStatus(runId);
          if (st.status === 'completed' || st.status === 'failed') return st;
          attempts++;
        }
        return await getOptimizationStatus(runId);
      };

      const [bFinal, aFinal] = await Promise.all([poll(bRes.run_id), poll(aRes.run_id)]);
      setBaselineData(bFinal);
      setAdaptiqData(aFinal);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const calculateAdvantage = () => {
    if (!baselineData?.best_fitness || !adaptiqData?.best_fitness) return null;
    const diff = baselineData.best_fitness - adaptiqData.best_fitness;
    const pct = (diff / baselineData.best_fitness) * 100;
    return { diff, pct };
  };

  const adv = calculateAdvantage();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <GitCompare size={22} color="#06b6d4" />
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Side-by-Side Comparison</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Execute Baseline GA vs AdaptIQ-R on identical topology and compare trajectories</p>
        </div>
      </div>

      {error && (
        <div style={{ padding: '0.75rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, color: '#ef4444', fontSize: 13 }}>
          {error}
        </div>
      )}

      {/* Control bar */}
      <div className="card" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
        <div style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
          <div>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', textTransform: 'uppercase', fontWeight: 600 }}>Generations: {generations}</label>
            <input type="range" min={20} max={150} value={generations} onChange={(e) => setGenerations(Number(e.target.value))} style={{ width: 140, accentColor: '#06b6d4' }} />
          </div>
          <div>
            <label style={{ fontSize: 11, color: '#64748b', display: 'block', textTransform: 'uppercase', fontWeight: 600 }}>Population: {popSize}</label>
            <input type="range" min={20} max={120} value={popSize} onChange={(e) => setPopSize(Number(e.target.value))} style={{ width: 140, accentColor: '#10b981' }} />
          </div>
          <div style={{ fontSize: 12, color: '#94a3b8' }}>
            Scenario: <strong style={{ color: scenario ? '#10b981' : '#ef4444' }}>{scenario ? `${scenario.node_count} Nodes (Seed ${scenario.seed})` : 'None'}</strong>
          </div>
        </div>

        <button onClick={runSideBySide} disabled={loading || !scenario} className="btn btn-primary" style={{ padding: '0.65rem 1.5rem' }}>
          <Play size={14} />
          {loading ? 'Evaluating Algorithms...' : 'Run Direct Comparison'}
        </button>
      </div>

      {adv && (
        <div style={{
          padding: '1.25rem',
          borderRadius: 8,
          background: adv.pct >= 0 ? 'rgba(16,185,129,0.08)' : 'rgba(239,68,68,0.08)',
          border: `1px solid ${adv.pct >= 0 ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ fontSize: 12, color: '#94a3b8' }}>Outcome Summary (Lower Cost / Fitness = Superior Route)</div>
            <div style={{ fontSize: '1.35rem', fontWeight: 800, color: adv.pct >= 0 ? '#10b981' : '#ef4444', fontFamily: 'JetBrains Mono, monospace' }}>
              AdaptIQ-R {adv.pct >= 0 ? `outperforms Baseline by ${adv.pct.toFixed(2)}%` : `trails Baseline by ${Math.abs(adv.pct).toFixed(2)}%`}
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#64748b', textAlign: 'right' }}>
            Baseline: {baselineData.best_fitness.toFixed(4)}<br/>
            AdaptIQ-R: {adaptiqData.best_fitness.toFixed(4)}
          </div>
        </div>
      )}

      {/* Grid of Results */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Baseline GA */}
        <div className="card">
          <div className="card-header">
            <div className="card-title">Standard Baseline GA</div>
            <span style={{ fontSize: 11, color: '#64748b' }}>Fixed Mutation (0.15)</span>
          </div>
          {baselineData ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                <div style={{ padding: '0.5rem', background: '#0d131f', borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Best Fitness</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#64748b', fontFamily: 'monospace' }}>{baselineData.best_fitness?.toFixed(4)}</div>
                </div>
                <div style={{ padding: '0.5rem', background: '#0d131f', borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Distance (km)</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#64748b', fontFamily: 'monospace' }}>{baselineData.total_distance?.toFixed(1) || '—'}</div>
                </div>
              </div>
              <FitnessChart history={baselineData.history || []} />
            </>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569', fontSize: 13 }}>
              Run comparison to view baseline results
            </div>
          )}
        </div>

        {/* AdaptIQ-R */}
        <div className="card">
          <div className="card-header">
            <div className="card-title" style={{ color: '#06b6d4' }}>AdaptIQ-R Engine</div>
            <span style={{ fontSize: 11, color: '#06b6d4', fontWeight: 600 }}>Mamdani Adaptive</span>
          </div>
          {adaptiqData ? (
            <>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                <div style={{ padding: '0.5rem', background: '#0d131f', borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Best Fitness</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#06b6d4', fontFamily: 'monospace' }}>{adaptiqData.best_fitness?.toFixed(4)}</div>
                </div>
                <div style={{ padding: '0.5rem', background: '#0d131f', borderRadius: 6 }}>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Distance (km)</div>
                  <div style={{ fontSize: 18, fontWeight: 700, color: '#06b6d4', fontFamily: 'monospace' }}>{adaptiqData.total_distance?.toFixed(1) || '—'}</div>
                </div>
              </div>
              <FitnessChart history={adaptiqData.history || []} />
            </>
          ) : (
            <div style={{ height: 220, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569', fontSize: 13 }}>
              Run comparison to view AdaptIQ-R results
            </div>
          )}
        </div>
      </div>

      {adaptiqData?.history && (
        <div className="card">
          <div className="card-header">
            <div className="card-title">AdaptIQ-R Dynamic Adaptation Profile</div>
          </div>
          <AdaptiveParamsChart history={adaptiqData.history} />
        </div>
      )}
    </div>
  );
}
