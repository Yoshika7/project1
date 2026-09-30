import React, { useState, useEffect, useRef } from 'react';
import {
  LineChart, Line, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const COLORS = {
  fitness:     '#06b6d4',
  avg:         '#3b82f6',
  diversity:   '#10b981',
  mutation:    '#f59e0b',
  exploration: '#8b5cf6',
  baseline:    '#64748b',
  adaptiq:     '#06b6d4',
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload || !payload.length) return null;
  return (
    <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, padding: '10px 14px', fontSize: 12 }}>
      <p style={{ color: '#94a3b8', marginBottom: 4 }}>Gen {label}</p>
      {payload.map((p) => (
        <p key={p.name} style={{ color: p.color, margin: '2px 0' }}>
          {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</strong>
        </p>
      ))}
    </div>
  );
};

export function FitnessChart({ history = [] }) {
  const data = history.map((m) => ({
    gen: m.generation,
    best: m.best_fitness,
    avg: m.avg_fitness,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <defs>
          <linearGradient id="fitGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor={COLORS.fitness} stopOpacity={0.25}/>
            <stop offset="95%" stopColor={COLORS.fitness} stopOpacity={0}/>
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="gen" stroke="#475569" tick={{ fontSize: 11 }} />
        <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
        <Area type="monotone" dataKey="best" name="Best Fitness" stroke={COLORS.fitness} fill="url(#fitGrad)" strokeWidth={2.5} dot={false} />
        <Line type="monotone" dataKey="avg" name="Avg Fitness" stroke={COLORS.avg} strokeWidth={1.5} dot={false} strokeDasharray="4 3" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function AdaptiveParamsChart({ history = [] }) {
  const data = history.map((m) => ({
    gen: m.generation,
    mutation: m.mutation_rate,
    exploration: m.exploration_level,
    diversity: m.population_diversity,
  }));

  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="gen" stroke="#475569" tick={{ fontSize: 11 }} />
        <YAxis stroke="#475569" tick={{ fontSize: 11 }} domain={[0, 1]} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
        <Line type="monotone" dataKey="mutation" name="Mutation Rate" stroke={COLORS.mutation} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="exploration" name="Exploration" stroke={COLORS.exploration} strokeWidth={2} dot={false} />
        <Line type="monotone" dataKey="diversity" name="Diversity" stroke={COLORS.diversity} strokeWidth={1.5} dot={false} strokeDasharray="5 3" />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function BenchmarkComparisonChart({ summary }) {
  if (!summary) return null;
  const data = [
    {
      metric: 'Recovered Fitness',
      Baseline: summary.baseline_mean_recovered_fitness,
      'AdaptIQ-R': summary.adaptiq_mean_recovered_fitness,
    },
    {
      metric: 'Rec. Generations',
      Baseline: summary.baseline_mean_recovery_gens,
      'AdaptIQ-R': summary.adaptiq_mean_recovery_gens,
    },
    {
      metric: 'Runtime (s)',
      Baseline: summary.baseline_mean_runtime_sec,
      'AdaptIQ-R': summary.adaptiq_mean_runtime_sec,
    },
  ];

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 0 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
        <XAxis dataKey="metric" stroke="#475569" tick={{ fontSize: 11 }} />
        <YAxis stroke="#475569" tick={{ fontSize: 11 }} />
        <Tooltip content={<CustomTooltip />} />
        <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
        <Bar dataKey="Baseline" fill={COLORS.baseline} radius={[4, 4, 0, 0]} />
        <Bar dataKey="AdaptIQ-R" fill={COLORS.adaptiq} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
