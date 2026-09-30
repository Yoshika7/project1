import React from 'react';
import { TrendingDown, TrendingUp, Minus } from 'lucide-react';

function Metric({ label, value, unit = '', color = '#06b6d4', mono = true }) {
  return (
    <div style={{ padding: '0.75rem 1rem', background: '#0d131f', borderRadius: '0.5rem', border: '1px solid #1e293b' }}>
      <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.06em' }}>{label}</div>
      <div style={{
        fontSize: '1.375rem',
        fontWeight: 700,
        color,
        fontFamily: mono ? 'JetBrains Mono, monospace' : 'Inter, sans-serif'
      }}>
        {value !== undefined && value !== null ? value : '—'}{unit}
      </div>
    </div>
  );
}

export default function MetricsDisplay({ status, scenario }) {
  const fmt = (v, d = 4) => (typeof v === 'number' ? v.toFixed(d) : '—');

  const isFeasible = status?.is_feasible;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
      {/* Status badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 0' }}>
        <div style={{
          width: 8, height: 8, borderRadius: '50%',
          background: status?.status === 'running' ? '#10b981' : status?.status === 'completed' ? '#06b6d4' : '#475569',
          boxShadow: status?.status === 'running' ? '0 0 0 4px rgba(16,185,129,0.2)' : 'none',
        }} />
        <span style={{ fontSize: 13, fontWeight: 600, color: '#94a3b8', textTransform: 'capitalize' }}>
          {status?.status || 'Idle'}
        </span>
        {status?.is_adaptive !== undefined && (
          <span style={{
            marginLeft: 'auto',
            fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 12,
            background: status.is_adaptive ? 'rgba(6,182,212,0.15)' : 'rgba(100,116,139,0.15)',
            color: status.is_adaptive ? '#06b6d4' : '#64748b',
            border: `1px solid ${status.is_adaptive ? 'rgba(6,182,212,0.3)' : 'rgba(100,116,139,0.3)'}`,
          }}>
            {status.is_adaptive ? 'FUZZY ADAPTIVE' : 'BASELINE GA'}
          </span>
        )}
      </div>

      {/* Core metrics grid */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
        <Metric label="Generation" value={status?.current_generation} color="#f8fafc" />
        <Metric label="Best Fitness" value={fmt(status?.best_fitness)} color="#06b6d4" />
        <Metric label="Diversity" value={fmt(status?.diversity)} color="#10b981" />
        <Metric label="Disruption Sev." value={fmt(status?.disruption_severity)} color={status?.disruption_severity > 0.3 ? '#ef4444' : '#94a3b8'} />
        <Metric label="Mutation Rate" value={fmt(status?.mutation_rate)} color="#f59e0b" />
        <Metric label="Exploration" value={fmt(status?.exploration_level)} color="#8b5cf6" />
      </div>

      {/* Feasibility indicator */}
      {status?.status && status.status !== 'idle' && (
        <div style={{
          padding: '0.6rem 1rem',
          borderRadius: '0.5rem',
          background: isFeasible ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
          border: `1px solid ${isFeasible ? 'rgba(16,185,129,0.3)' : 'rgba(239,68,68,0.3)'}`,
          fontSize: 13, color: isFeasible ? '#10b981' : '#ef4444',
          display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600
        }}>
          {isFeasible ? '✓' : '✗'} Route is {isFeasible ? 'FEASIBLE' : 'INFEASIBLE (rerouting…)'}
        </div>
      )}

      {/* Distance and time */}
      {status?.total_distance > 0 && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
          <Metric label="Distance (km)" value={status.total_distance?.toFixed(1)} color="#94a3b8" />
          <Metric label="Travel Time (min)" value={status.total_travel_time?.toFixed(1)} color="#94a3b8" />
        </div>
      )}
    </div>
  );
}
