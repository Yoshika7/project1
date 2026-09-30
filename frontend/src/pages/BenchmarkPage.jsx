import React, { useState } from 'react';
import { FlaskConical, Play } from 'lucide-react';
import { runBenchmark, getBenchmark } from '../services/api';
import { BenchmarkComparisonChart } from '../components/OptimizationCharts';

export default function BenchmarkPage() {
  const [nodeCount, setNodeCount] = useState(20);
  const [seeds, setSeeds] = useState('42, 123, 456');
  const [initGens, setInitGens] = useState(40);
  const [recGens, setRecGens] = useState(40);
  const [popSize, setPopSize] = useState(60);
  const [loading, setLoading] = useState(false);
  const [benchId, setBenchId] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleRun = async () => {
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const parsedSeeds = seeds.split(',').map((s) => parseInt(s.trim(), 10)).filter((n) => !isNaN(n));
      const startRes = await runBenchmark({
        node_count: nodeCount,
        seeds: parsedSeeds,
        initial_gens: initGens,
        recovery_gens: recGens,
        pop_size: popSize,
      });
      setBenchId(startRes.benchmark_id);

      // Poll until complete
      const maxWait = 300;
      let elapsed = 0;
      while (elapsed < maxWait) {
        await new Promise((r) => setTimeout(r, 3000));
        elapsed += 3;
        const status = await getBenchmark(startRes.benchmark_id);
        if (status.status === 'completed') {
          setResult(status.summary);
          break;
        } else if (status.status === 'failed') {
          throw new Error(status.error || 'Benchmark failed');
        }
      }
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const MetaRow = ({ label, base, adapt, lowerBetter = true }) => {
    const betterIsAdapt = lowerBetter ? adapt < base : adapt > base;
    return (
      <tr>
        <td style={{ padding: '8px 12px', color: '#94a3b8', fontSize: 13 }}>{label}</td>
        <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: 'monospace', fontSize: 13, color: '#64748b' }}>{typeof base === 'number' ? base.toFixed(4) : base}</td>
        <td style={{ padding: '8px 12px', textAlign: 'right', fontFamily: 'monospace', fontSize: 13, color: betterIsAdapt ? '#10b981' : '#ef4444', fontWeight: 700 }}>{typeof adapt === 'number' ? adapt.toFixed(4) : adapt}</td>
      </tr>
    );
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <FlaskConical size={22} color="#10b981" />
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Benchmark Suite</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Head-to-head: Baseline GA vs AdaptIQ-R across multiple seeds</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '300px 1fr', gap: '1.5rem', alignItems: 'start' }}>
        {/* Config */}
        <div className="card">
          <div className="card-header"><div className="card-title">Configuration</div></div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Network Size</label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.4rem', marginTop: 6 }}>
              {[10, 20, 50, 100].map((n) => (
                <button key={n} onClick={() => setNodeCount(n)} style={{ padding: '0.5rem', borderRadius: 6, fontSize: 12, fontWeight: 700, cursor: 'pointer', border: `1px solid ${nodeCount === n ? '#10b981' : '#334155'}`, background: nodeCount === n ? 'rgba(16,185,129,0.1)' : '#1e293b', color: nodeCount === n ? '#10b981' : '#94a3b8' }}>{n}</button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>Seeds (comma-separated)</label>
            <input value={seeds} onChange={(e) => setSeeds(e.target.value)}
              style={{ width: '100%', marginTop: 6, padding: '0.55rem 0.75rem', borderRadius: 6, background: '#0d131f', border: '1px solid #334155', color: '#f8fafc', fontSize: 13, fontFamily: 'monospace', outline: 'none' }} />
          </div>

          {[['Initial Gens', initGens, setInitGens, '#06b6d4'], ['Recovery Gens', recGens, setRecGens, '#f59e0b'], ['Population', popSize, setPopSize, '#8b5cf6']].map(([label, val, setter, color]) => (
            <div key={label} style={{ marginBottom: '0.75rem' }}>
              <label style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', fontWeight: 600 }}>{label}: {val}</label>
              <input type="range" min={10} max={200} step={10} value={val} onChange={(e) => setter(Number(e.target.value))} style={{ width: '100%', marginTop: 4, accentColor: color }} />
            </div>
          ))}

          <button onClick={handleRun} disabled={loading} className="btn btn-emerald" style={{ width: '100%' }}>
            <Play size={14} />
            {loading ? `Running… ${benchId ? `(${benchId.slice(-6)})` : ''}` : 'Run Benchmark'}
          </button>

          {error && <div style={{ marginTop: '0.5rem', fontSize: 12, color: '#ef4444', padding: '0.4rem', background: 'rgba(239,68,68,0.1)', borderRadius: 6 }}>{error}</div>}

          <div style={{ marginTop: '0.75rem', padding: '0.6rem', background: '#0d131f', borderRadius: 6, fontSize: 11, color: '#475569' }}>
            ⚠ Benchmarks run real algorithms. Larger grids and more seeds take longer.
          </div>
        </div>

        {/* Results */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {result ? (
            <>
              {/* Improvement badge */}
              <div style={{
                padding: '1rem 1.5rem', borderRadius: 10,
                background: result.adaptiq_fitness_improvement_pct > 0 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                border: `1px solid ${result.adaptiq_fitness_improvement_pct > 0 ? 'rgba(16,185,129,0.35)' : 'rgba(239,68,68,0.35)'}`,
                display: 'flex', alignItems: 'center', justifyContent: 'space-between'
              }}>
                <div>
                  <div style={{ fontSize: 13, color: '#94a3b8' }}>AdaptIQ-R fitness improvement over Baseline</div>
                  <div style={{ fontSize: '2rem', fontWeight: 800, fontFamily: 'monospace', color: result.adaptiq_fitness_improvement_pct > 0 ? '#10b981' : '#ef4444' }}>
                    {result.adaptiq_fitness_improvement_pct > 0 ? '+' : ''}{result.adaptiq_fitness_improvement_pct.toFixed(2)}%
                  </div>
                </div>
                <div style={{ textAlign: 'right', fontSize: 12, color: '#64748b' }}>
                  <div>Seeds evaluated: {result.seeds_evaluated?.join(', ')}</div>
                  <div>Network size: {result.node_count} nodes</div>
                </div>
              </div>

              {/* Comparison chart */}
              <div className="card">
                <div className="card-header"><div className="card-title">Metric Comparison</div></div>
                <BenchmarkComparisonChart summary={result} />
              </div>

              {/* Detail table */}
              <div className="card">
                <div className="card-header"><div className="card-title">Statistical Summary</div></div>
                <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ borderBottom: '1px solid #1e293b' }}>
                      <th style={{ textAlign: 'left', padding: '8px 12px', fontSize: 11, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Metric</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', fontSize: 11, color: '#64748b', fontWeight: 700, textTransform: 'uppercase' }}>Baseline GA</th>
                      <th style={{ textAlign: 'right', padding: '8px 12px', fontSize: 11, color: '#10b981', fontWeight: 700, textTransform: 'uppercase' }}>AdaptIQ-R</th>
                    </tr>
                  </thead>
                  <tbody>
                    <MetaRow label="Mean Recovered Fitness" base={result.baseline_mean_recovered_fitness} adapt={result.adaptiq_mean_recovered_fitness} lowerBetter={true} />
                    <MetaRow label="Std Dev Fitness" base={result.baseline_std_fitness} adapt={result.adaptiq_std_fitness} lowerBetter={true} />
                    <MetaRow label="Mean Recovery Generations" base={result.baseline_mean_recovery_gens} adapt={result.adaptiq_mean_recovery_gens} lowerBetter={true} />
                    <MetaRow label="Mean Runtime (s)" base={result.baseline_mean_runtime_sec} adapt={result.adaptiq_mean_runtime_sec} lowerBetter={true} />
                  </tbody>
                </table>
                <div style={{ marginTop: '0.75rem', fontSize: 11, color: '#475569', fontStyle: 'italic', paddingLeft: '0.75rem' }}>
                  <span style={{ color: '#10b981' }}>Green</span> = AdaptIQ-R better. Results are actual algorithm outputs — not manipulated.
                </div>
              </div>
            </>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 300, color: '#475569', fontSize: 14, border: '2px dashed #1e293b', borderRadius: 10 }}>
              {loading ? 'Running benchmark across seeds…' : 'Configure and run a benchmark to see results'}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
