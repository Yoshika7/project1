import React from 'react';
import { Zap, AlertTriangle, BookOpen, TrendingUp } from 'lucide-react';

/**
 * Fuzzy Controller Diagnostic Panel.
 * Shows real-time inputs, activated rules, and defuzzified outputs.
 * All values come from actual Mamdani inference — nothing is faked.
 */
export default function FuzzyDiagnostic({ status }) {
  const rules = {
    R1: 'Diversity LOW + Improvement LOW → Mutation HIGH, Exploration HIGH',
    R2: 'Diversity LOW + Improvement MED → Mutation HIGH, Exploration MED',
    R3: 'Diversity HIGH + Improvement HIGH → Mutation LOW, Exploration LOW',
    R4: 'Disruption HIGH → Mutation HIGH, Exploration HIGH',
    R5: 'Disruption MED + Improvement LOW → Mutation HIGH, Exploration MED',
    R6: 'Disruption LOW + Improvement HIGH → Mutation LOW, Exploration LOW',
    R7: 'Diversity MED + Improvement MED → Mutation MED, Exploration MED',
    R8: 'Diversity HIGH + Improvement LOW → Mutation MED, Exploration LOW',
    R9: 'Disruption LOW + Diversity LOW → Mutation MED, Exploration MED',
  };

  const activated = status?.activated_rules || [];

  const GaugeBar = ({ value, color, label, unit = '' }) => (
    <div style={{ marginBottom: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12, color: '#94a3b8' }}>
        <span>{label}</span>
        <span style={{ color, fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>
          {typeof value === 'number' ? value.toFixed(4) : '—'}{unit}
        </span>
      </div>
      <div style={{ background: '#1e293b', borderRadius: 4, height: 6, overflow: 'hidden' }}>
        <div style={{
          width: `${Math.min(100, (value || 0) * 100)}%`,
          height: '100%',
          background: color,
          borderRadius: 4,
          transition: 'width 0.4s ease'
        }} />
      </div>
    </div>
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
      {/* Inputs */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <BookOpen size={16} color="#06b6d4" />
            Fuzzy Inputs
          </div>
        </div>
        <GaugeBar value={status?.diversity} color="#10b981" label="Population Diversity" />
        <GaugeBar value={status?.disruption_severity} color="#ef4444" label="Disruption Severity" />
        <div style={{ marginBottom: 10 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4, fontSize: 12, color: '#94a3b8' }}>
            <span>Fitness Improvement</span>
            <span style={{ color: '#6366f1', fontFamily: 'monospace', fontWeight: 600 }}>
              {status?.history?.length > 1 ? (status.history[status.history.length - 1]?.fitness_improvement || 0).toFixed(4) : '—'}
            </span>
          </div>
          <div style={{ background: '#1e293b', borderRadius: 4, height: 6, overflow: 'hidden' }}>
            <div style={{
              width: `${Math.min(100, ((status?.history?.[status.history.length - 1]?.fitness_improvement || 0)) * 100)}%`,
              height: '100%', background: '#6366f1', borderRadius: 4, transition: 'width 0.4s ease'
            }} />
          </div>
        </div>
      </div>

      {/* Outputs */}
      <div className="card">
        <div className="card-header">
          <div className="card-title">
            <TrendingUp size={16} color="#f59e0b" />
            Fuzzy Outputs
          </div>
        </div>
        <GaugeBar value={status?.mutation_rate} color="#f59e0b" label="Mutation Rate" />
        <GaugeBar value={status?.exploration_level} color="#8b5cf6" label="Exploration Level" />
        <div style={{ fontSize: 11, color: '#64748b', marginTop: 8, fontFamily: 'monospace', background: '#0d1526', padding: '6px 10px', borderRadius: 6 }}>
          Defuzzification: Centroid Method (Mamdani)
        </div>
      </div>

      {/* Activated Rules */}
      <div className="card" style={{ gridColumn: '1 / -1' }}>
        <div className="card-header">
          <div className="card-title">
            <Zap size={16} color="#f59e0b" />
            Activated Fuzzy Rules
          </div>
          <span style={{ fontSize: 12, color: '#64748b' }}>{activated.length} rules firing</span>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {Object.keys(rules).map((ruleId) => {
            const isActive = activated.includes(ruleId);
            return (
              <div
                key={ruleId}
                title={rules[ruleId]}
                style={{
                  padding: '6px 12px',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                  fontFamily: 'JetBrains Mono, monospace',
                  background: isActive ? 'rgba(245, 158, 11, 0.15)' : '#1e293b',
                  border: `1px solid ${isActive ? 'rgba(245, 158, 11, 0.5)' : '#334155'}`,
                  color: isActive ? '#f59e0b' : '#475569',
                  cursor: 'help',
                  transition: 'all 0.2s ease',
                  boxShadow: isActive ? '0 0 8px rgba(245,158,11,0.2)' : 'none',
                }}
              >
                {ruleId}
              </div>
            );
          })}
        </div>
        {activated.length > 0 && (
          <div style={{ marginTop: '0.75rem', fontSize: 12, color: '#64748b' }}>
            {activated.map((r) => (
              <div key={r} style={{ padding: '2px 0', color: '#94a3b8' }}>
                <span style={{ color: '#f59e0b', fontWeight: 600 }}>{r}</span>: {rules[r]}
              </div>
            ))}
          </div>
        )}
        {activated.length === 0 && (
          <p style={{ fontSize: 12, color: '#475569', marginTop: 8 }}>No rules active — optimization not yet started.</p>
        )}
      </div>
    </div>
  );
}
