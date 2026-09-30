import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Network, Cpu, Zap, BarChart3, GitCompare, FlaskConical } from 'lucide-react';

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/scenario', label: 'Scenario', icon: Network },
  { to: '/optimization', label: 'Optimize', icon: Cpu },
  { to: '/disruption', label: 'Disruption Lab', icon: Zap },
  { to: '/comparison', label: 'Comparison', icon: GitCompare },
  { to: '/analytics', label: 'Analytics', icon: BarChart3 },
  { to: '/benchmark', label: 'Benchmark', icon: FlaskConical },
];

export default function Navigation() {
  return (
    <nav style={{
      background: '#0d131f',
      borderRight: '1px solid #1e293b',
      width: 220,
      minHeight: '100vh',
      display: 'flex',
      flexDirection: 'column',
      padding: '1.5rem 0',
      position: 'fixed',
      top: 0,
      left: 0,
    }}>
      {/* Logo */}
      <div style={{ padding: '0 1.25rem 1.5rem', borderBottom: '1px solid #1e293b' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
          <div style={{ width: 28, height: 28, background: 'linear-gradient(135deg, #06b6d4, #3b82f6)', borderRadius: 8, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 13, fontWeight: 800, color: 'white' }}>
            A
          </div>
          <span style={{ fontSize: '1.125rem', fontWeight: 800, color: '#f8fafc', letterSpacing: '-0.01em' }}>AdaptIQ-R</span>
        </div>
        <p style={{ fontSize: '0.7rem', color: '#64748b', marginLeft: 36, lineHeight: 1.4 }}>
          Adaptive Route Optimization
        </p>
      </div>

      {/* Nav Links */}
      <div style={{ flex: 1, padding: '0.75rem 0.75rem', display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
        {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            style={({ isActive }) => ({
              display: 'flex',
              alignItems: 'center',
              gap: '0.65rem',
              padding: '0.6rem 0.875rem',
              borderRadius: '0.5rem',
              fontSize: '0.875rem',
              fontWeight: 500,
              textDecoration: 'none',
              transition: 'all 0.15s ease',
              background: isActive ? 'rgba(6, 182, 212, 0.1)' : 'transparent',
              color: isActive ? '#06b6d4' : '#94a3b8',
              borderLeft: isActive ? '2px solid #06b6d4' : '2px solid transparent',
            })}
          >
            {({ isActive }) => (
              <>
                <Icon size={15} color={isActive ? '#06b6d4' : '#64748b'} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </div>

      {/* Footer badge */}
      <div style={{ padding: '1rem 1.25rem', borderTop: '1px solid #1e293b' }}>
        <div style={{ fontSize: '0.7rem', color: '#475569', fontFamily: 'JetBrains Mono, monospace' }}>
          CI Research v1.0<br/>
          <span style={{ color: '#10b981' }}>● Fuzzy-GA Engine Active</span>
        </div>
      </div>
    </nav>
  );
}
