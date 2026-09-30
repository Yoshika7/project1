import React from 'react';
import { LayoutDashboard, Network, Cpu, Zap, GitCompare, BarChart3, FlaskConical, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';
import { useOptimizationPoller } from '../hooks/useOptimization';
import { FitnessChart, AdaptiveParamsChart } from '../components/OptimizationCharts';

const StepCard = ({ number, title, icon: Icon, color, to, description }) => (
  <Link to={to} style={{ textDecoration: 'none' }}>
    <div style={{ background: '#121826', border: '1px solid #1e293b', borderRadius: 10, padding: '1rem 1.25rem', cursor: 'pointer', transition: 'all 0.15s', display: 'flex', alignItems: 'flex-start', gap: '0.875rem' }}
      onMouseEnter={(e) => { e.currentTarget.style.borderColor = color; e.currentTarget.style.transform = 'translateY(-1px)'; }}
      onMouseLeave={(e) => { e.currentTarget.style.borderColor = '#1e293b'; e.currentTarget.style.transform = 'none'; }}>
      <div style={{ width: 36, height: 36, background: `${color}20`, borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
        <Icon size={16} color={color} />
      </div>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 11, color: color, fontWeight: 700, marginBottom: 2, fontFamily: 'monospace' }}>Step {number}</div>
        <div style={{ fontWeight: 700, color: '#f8fafc', fontSize: 14 }}>{title}</div>
        <p style={{ fontSize: 12, color: '#64748b', marginTop: 4, lineHeight: 1.4 }}>{description}</p>
      </div>
      <ArrowRight size={14} color="#334155" />
    </div>
  </Link>
);

export default function Dashboard({ scenario, runId }) {
  const { status } = useOptimizationPoller(runId, 1000);
  const history = status?.history || [];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Hero */}
      <div style={{ background: 'linear-gradient(135deg, #0d131f 0%, #0f1e2e 100%)', border: '1px solid #1e293b', borderRadius: 12, padding: '1.5rem 2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <div style={{ width: 36, height: 36, background: 'linear-gradient(135deg, #06b6d4, #3b82f6)', borderRadius: 10, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18, fontWeight: 900, color: 'white' }}>A</div>
          <div>
            <h1 style={{ fontSize: '1.75rem', fontWeight: 900, color: '#f8fafc', margin: 0, letterSpacing: '-0.02em' }}>
              AdaptIQ-R
            </h1>
            <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Adaptive Route Optimization Under Disruption</p>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: '0.5rem' }}>
            <span className="badge badge-cyan">Evolutionary AI</span>
            <span className="badge badge-emerald">Fuzzy Logic</span>
            <span className="badge badge-amber">Disruption Recovery</span>
          </div>
        </div>
        <p style={{ color: '#94a3b8', fontSize: 14, maxWidth: 700, lineHeight: 1.6, margin: 0 }}>
          A computational intelligence prototype combining a <strong style={{ color: '#f8fafc' }}>Genetic Algorithm</strong> with a <strong style={{ color: '#f8fafc' }}>pure Python Mamdani Fuzzy Controller</strong> for real-time adaptive route optimization. Demonstrates dynamic recovery from road blocks, traffic surges, and vehicle failures on synthetic networks.
        </p>
      </div>

      {/* System Status Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
        {[
          { label: 'Scenario', value: scenario ? `${scenario.node_count}N / ${scenario.edges?.length}E` : 'Not Generated', color: scenario ? '#10b981' : '#475569' },
          { label: 'Active Run', value: runId ? runId.slice(0, 12) + '…' : 'None', color: runId ? '#06b6d4' : '#475569' },
          { label: 'Status', value: status?.status || 'Idle', color: status?.status === 'running' ? '#10b981' : '#64748b' },
          { label: 'Best Fitness', value: status?.best_fitness ? status.best_fitness.toFixed(4) : '—', color: '#f59e0b' },
        ].map(({ label, value, color }) => (
          <div key={label} style={{ background: '#121826', border: '1px solid #1e293b', borderRadius: 10, padding: '0.875rem 1rem' }}>
            <div style={{ fontSize: 11, color: '#475569', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.06em', marginBottom: 4 }}>{label}</div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontWeight: 700, color, fontSize: 14 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Two-col: workflow steps + live charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Workflow */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
          <h2 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>Research Workflow</h2>
          <StepCard number={1} title="Generate Scenario" icon={Network} color="#06b6d4" to="/scenario" description="Configure node count and seed for a reproducible synthetic road network." />
          <StepCard number={2} title="Run Optimizer" icon={Cpu} color="#10b981" to="/optimization" description="Start Baseline GA or Fuzzy-Adaptive AdaptIQ-R. Watch real-time convergence." />
          <StepCard number={3} title="Inject Disruption" icon={Zap} color="#f59e0b" to="/disruption" description="Block roads, surge traffic, change priorities, or simulate vehicle failure." />
          <StepCard number={4} title="Benchmark Results" icon={FlaskConical} color="#8b5cf6" to="/benchmark" description="Compare Baseline vs AdaptIQ-R across multiple seeds. Honest reporting." />
        </div>

        {/* Live charts */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <h2 style={{ fontSize: '0.875rem', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', margin: 0 }}>Live Telemetry</h2>
          <div className="card">
            <div className="card-title" style={{ marginBottom: '0.75rem', fontSize: 13 }}>Fitness Convergence</div>
            {history.length > 0 ? <FitnessChart history={history} /> : (
              <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#334155', fontSize: 13 }}>No run active — start an optimization to see live data</div>
            )}
          </div>
          <div className="card">
            <div className="card-title" style={{ marginBottom: '0.75rem', fontSize: 13 }}>Fuzzy Adaptive Parameters</div>
            {history.length > 0 ? <AdaptiveParamsChart history={history} /> : (
              <div style={{ height: 180, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#334155', fontSize: 13 }}>Mutation rate, exploration level, and diversity appear here during AdaptIQ-R runs</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
