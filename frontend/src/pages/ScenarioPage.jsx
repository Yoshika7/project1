import React, { useState } from 'react';
import { Network, Play, Settings } from 'lucide-react';
import { generateScenario } from '../services/api';
import NetworkGraph from '../components/NetworkGraph';

export default function ScenarioPage({ scenario, setScenario }) {
  const [nodeCount, setNodeCount] = useState(20);
  const [seed, setSeed] = useState(42);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const s = await generateScenario(nodeCount, seed);
      setScenario(s);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  const nodeOptions = [10, 20, 50, 100];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Network size={22} color="#06b6d4" />
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Scenario Builder</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Generate a reproducible synthetic road network</p>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '1.5rem' }}>
        {/* Configuration Panel */}
        <div className="card">
          <div className="card-header">
            <div className="card-title"><Settings size={16} color="#94a3b8" /> Configuration</div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Network Size
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
              {nodeOptions.map((n) => (
                <button
                  key={n}
                  onClick={() => setNodeCount(n)}
                  style={{
                    padding: '0.6rem 0',
                    borderRadius: 6,
                    border: `1px solid ${nodeCount === n ? '#06b6d4' : '#334155'}`,
                    background: nodeCount === n ? 'rgba(6,182,212,0.1)' : '#1e293b',
                    color: nodeCount === n ? '#06b6d4' : '#94a3b8',
                    fontWeight: 600, fontSize: 13, cursor: 'pointer', transition: 'all 0.15s'
                  }}
                >
                  {n}
                </button>
              ))}
            </div>
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: 12, color: '#94a3b8', marginBottom: 8, fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Random Seed
            </label>
            <input
              type="number"
              value={seed}
              onChange={(e) => setSeed(Number(e.target.value))}
              style={{
                width: '100%', padding: '0.6rem 0.875rem', borderRadius: 6,
                background: '#0d131f', border: '1px solid #334155', color: '#f8fafc',
                fontSize: 14, fontFamily: 'JetBrains Mono, monospace', outline: 'none'
              }}
            />
            <p style={{ fontSize: 11, color: '#475569', marginTop: 4 }}>Same seed → same topology (reproducible)</p>
          </div>

          <button
            onClick={handleGenerate}
            disabled={loading}
            className="btn btn-primary"
            style={{ width: '100%', padding: '0.75rem' }}
          >
            <Play size={15} />
            {loading ? 'Generating…' : 'Generate Network'}
          </button>

          {error && (
            <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.875rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 6, fontSize: 12, color: '#ef4444' }}>
              {error}
            </div>
          )}

          {scenario && (
            <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#0d131f', borderRadius: 8, border: '1px solid #1e293b' }}>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4, fontWeight: 700, textTransform: 'uppercase' }}>Current Scenario</div>
              {[
                ['ID', scenario.id],
                ['Nodes', scenario.node_count],
                ['Edges', scenario.edges?.length],
                ['Seed', scenario.seed],
                ['Depot', scenario.depot_id],
              ].map(([k, v]) => (
                <div key={k} style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, padding: '3px 0', color: '#94a3b8', borderBottom: '1px solid #1e293b' }}>
                  <span>{k}</span>
                  <span style={{ color: '#f8fafc', fontFamily: 'JetBrains Mono, monospace' }}>{v}</span>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Network Visualization */}
        <div>
          <NetworkGraph scenario={scenario} height={520} />
        </div>
      </div>
    </div>
  );
}
