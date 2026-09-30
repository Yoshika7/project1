import React, { useState } from 'react';
import { Zap, AlertTriangle, Car, TrendingUp } from 'lucide-react';
import { blockRoad, surgeTraffic, changePriority, simulateVehicleFailure, adaptOptimization } from '../services/api';
import { useOptimizationPoller } from '../hooks/useOptimization';
import NetworkGraph from '../components/NetworkGraph';
import MetricsDisplay from '../components/MetricsDisplay';
import FuzzyDiagnostic from '../components/FuzzyDiagnostic';

export default function DisruptionPage({ scenario, runId }) {
  const [blockSource, setBlockSource] = useState('');
  const [blockTarget, setBlockTarget] = useState('');
  const [trafficEdges, setTrafficEdges] = useState('');
  const [trafficFactor, setTrafficFactor] = useState(2.5);
  const [priorityNode, setPriorityNode] = useState('');
  const [priorityLevel, setPriorityLevel] = useState(3);
  const [capacityLoss, setCapacityLoss] = useState(0.5);
  const [recoveryGens, setRecoveryGens] = useState(60);

  const [lastSeverity, setLastSeverity] = useState(null);
  const [disruptionLog, setDisruptionLog] = useState([]);
  const [error, setError] = useState(null);

  const { status } = useOptimizationPoller(runId, 800);

  const logEvent = (type, severity) => {
    setDisruptionLog(prev => [{
      type, severity: severity.severity,
      time: new Date().toLocaleTimeString()
    }, ...prev].slice(0, 8));
    setLastSeverity(severity);
  };

  const guard = () => {
    if (!runId) { setError('Start an optimization run first.'); return false; }
    setError(null);
    return true;
  };

  const handleBlock = async () => {
    if (!guard()) return;
    try {
      const sev = await blockRoad(runId, Number(blockSource), Number(blockTarget));
      logEvent(`Road Block: ${blockSource}→${blockTarget}`, sev);
    } catch (e) { setError(e.message); }
  };

  const handleTraffic = async () => {
    if (!guard()) return;
    try {
      const pairs = trafficEdges.split(',').map(p => p.trim().split('-').map(Number));
      const sev = await surgeTraffic(runId, pairs, trafficFactor);
      logEvent(`Traffic Surge ×${trafficFactor}`, sev);
    } catch (e) { setError(e.message); }
  };

  const handlePriority = async () => {
    if (!guard()) return;
    try {
      const sev = await changePriority(runId, Number(priorityNode), Number(priorityLevel));
      logEvent(`Priority Change: Node ${priorityNode} → P${priorityLevel}`, sev);
    } catch (e) { setError(e.message); }
  };

  const handleVehicle = async () => {
    if (!guard()) return;
    try {
      const sev = await simulateVehicleFailure(runId, capacityLoss);
      logEvent(`Vehicle Failure: −${(capacityLoss * 100).toFixed(0)}% capacity`, sev);
    } catch (e) { setError(e.message); }
  };

  const handleAdapt = async () => {
    if (!guard()) return;
    try {
      await adaptOptimization(runId, recoveryGens);
    } catch (e) { setError(e.message); }
  };

  const SeverityBar = ({ value }) => (
    <div style={{ marginTop: 8 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#64748b', marginBottom: 3 }}>
        <span>Severity</span>
        <span style={{ color: value > 0.5 ? '#ef4444' : '#f59e0b', fontWeight: 700 }}>
          {value?.toFixed(4)}
        </span>
      </div>
      <div style={{ background: '#1e293b', borderRadius: 4, height: 6 }}>
        <div style={{ width: `${(value || 0) * 100}%`, height: '100%', background: value > 0.5 ? '#ef4444' : '#f59e0b', borderRadius: 4, transition: 'width 0.4s' }} />
      </div>
    </div>
  );

  const DisruptionCard = ({ icon: Icon, title, color, children }) => (
    <div className="card">
      <div className="card-header">
        <div className="card-title"><Icon size={15} color={color} />{title}</div>
        <span className="badge" style={{ background: `${color}20`, color, border: `1px solid ${color}50`, fontSize: 10, padding: '2px 8px', borderRadius: 999 }}>DISRUPT</span>
      </div>
      {children}
    </div>
  );

  const inp = (value, onChange, placeholder, type = 'text') => (
    <input type={type} value={value} onChange={(e) => onChange(e.target.value)} placeholder={placeholder}
      style={{ width: '100%', padding: '0.55rem 0.75rem', borderRadius: 6, background: '#0d131f', border: '1px solid #334155', color: '#f8fafc', fontSize: 13, fontFamily: 'JetBrains Mono, monospace', marginBottom: '0.5rem', outline: 'none' }} />
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <Zap size={22} color="#f59e0b" />
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 700, color: '#f8fafc', margin: 0 }}>Disruption Lab</h1>
          <p style={{ fontSize: '0.875rem', color: '#64748b', margin: 0 }}>Inject real-time environmental disruptions and trigger adaptive recovery</p>
        </div>
      </div>

      {error && <div style={{ padding: '0.75rem 1rem', background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.3)', borderRadius: 8, fontSize: 13, color: '#ef4444' }}>{error}</div>}

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Row 1 */}
        <DisruptionCard icon={AlertTriangle} title="Road Block" color="#ef4444">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <input type="number" value={blockSource} onChange={(e) => setBlockSource(e.target.value)} placeholder="Source node ID"
              style={{ padding: '0.55rem 0.75rem', borderRadius: 6, background: '#0d131f', border: '1px solid #334155', color: '#f8fafc', fontSize: 13, outline: 'none' }} />
            <input type="number" value={blockTarget} onChange={(e) => setBlockTarget(e.target.value)} placeholder="Target node ID"
              style={{ padding: '0.55rem 0.75rem', borderRadius: 6, background: '#0d131f', border: '1px solid #334155', color: '#f8fafc', fontSize: 13, outline: 'none' }} />
          </div>
          <button onClick={handleBlock} className="btn btn-rose" style={{ width: '100%', marginTop: '0.5rem' }}>Block Road</button>
        </DisruptionCard>

        <DisruptionCard icon={TrendingUp} title="Traffic Surge" color="#f59e0b">
          {inp(trafficEdges, setTrafficEdges, 'e.g. 1-2, 3-4 (source-target pairs)')}
          <div style={{ marginBottom: '0.5rem' }}>
            <label style={{ fontSize: 11, color: '#64748b' }}>Factor: {trafficFactor}×</label>
            <input type="range" min={1.5} max={5} step={0.5} value={trafficFactor}
              onChange={(e) => setTrafficFactor(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#f59e0b' }} />
          </div>
          <button onClick={handleTraffic} className="btn" style={{ width: '100%', background: '#92400e', color: '#fde68a', border: '1px solid #d97706' }}>Surge Traffic</button>
        </DisruptionCard>

        <DisruptionCard icon={Car} title="Priority Change" color="#8b5cf6">
          {inp(priorityNode, setPriorityNode, 'Node ID to reprioritize', 'number')}
          <div style={{ marginBottom: '0.5rem' }}>
            <label style={{ fontSize: 11, color: '#64748b' }}>Priority: {priorityLevel}</label>
            <input type="range" min={1} max={5} value={priorityLevel}
              onChange={(e) => setPriorityLevel(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#8b5cf6' }} />
          </div>
          <button onClick={handlePriority} className="btn" style={{ width: '100%', background: '#4c1d95', color: '#c4b5fd', border: '1px solid #7c3aed' }}>Change Priority</button>
        </DisruptionCard>

        <DisruptionCard icon={Car} title="Vehicle Failure" color="#ef4444">
          <div style={{ marginBottom: '0.75rem' }}>
            <label style={{ fontSize: 11, color: '#64748b' }}>Capacity Loss: {(capacityLoss * 100).toFixed(0)}%</label>
            <input type="range" min={0.1} max={1.0} step={0.1} value={capacityLoss}
              onChange={(e) => setCapacityLoss(Number(e.target.value))}
              style={{ width: '100%', accentColor: '#ef4444' }} />
          </div>
          <button onClick={handleVehicle} className="btn btn-rose" style={{ width: '100%' }}>Simulate Failure</button>
        </DisruptionCard>
      </div>

      {/* Recovery Action */}
      <div className="card" style={{ borderColor: '#064e3b', background: 'rgba(6,78,59,0.1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <div style={{ flex: 1 }}>
            <div style={{ fontWeight: 700, color: '#10b981', marginBottom: 4 }}>Continue Adaptive Recovery</div>
            <p style={{ fontSize: 12, color: '#64748b' }}>Run additional optimization after a disruption. The fuzzy controller will automatically adapt mutation and exploration.</p>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div>
              <label style={{ fontSize: 11, color: '#64748b' }}>Recovery Gens: {recoveryGens}</label>
              <input type="range" min={10} max={200} step={10} value={recoveryGens}
                onChange={(e) => setRecoveryGens(Number(e.target.value))}
                style={{ width: 120, accentColor: '#10b981', display: 'block', marginTop: 4 }} />
            </div>
            <button onClick={handleAdapt} className="btn btn-emerald">Adapt & Recover</button>
          </div>
        </div>
      </div>

      {/* Severity + Fuzzy */}
      {lastSeverity && (
        <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '1rem', alignItems: 'start' }}>
          <div className="card">
            <div style={{ fontWeight: 700, color: '#f8fafc', marginBottom: '0.75rem', fontSize: 14 }}>Severity Breakdown</div>
            {[
              ['Blocked Edge Ratio', lastSeverity.blocked_edge_ratio, '#ef4444'],
              ['Traffic Change', lastSeverity.normalized_traffic_change, '#f59e0b'],
              ['Priority Change', lastSeverity.normalized_priority_change, '#8b5cf6'],
              ['Vehicle Change', lastSeverity.vehicle_change, '#06b6d4'],
            ].map(([label, val, color]) => (
              <div key={label} style={{ marginBottom: 10 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 11, color: '#94a3b8', marginBottom: 3 }}>
                  <span>{label}</span>
                  <span style={{ color, fontFamily: 'monospace' }}>{val?.toFixed(4)}</span>
                </div>
                <div style={{ background: '#1e293b', borderRadius: 4, height: 5 }}>
                  <div style={{ width: `${(val || 0) * 100}%`, height: '100%', background: color, borderRadius: 4 }} />
                </div>
              </div>
            ))}
            <div style={{ marginTop: '0.75rem', padding: '0.6rem 0.875rem', background: 'rgba(239,68,68,0.1)', borderRadius: 6, border: '1px solid rgba(239,68,68,0.25)' }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Total Severity (S)</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 800, color: lastSeverity.severity > 0.5 ? '#ef4444' : '#f59e0b', fontFamily: 'monospace' }}>
                {lastSeverity.severity?.toFixed(4)}
              </div>
            </div>
          </div>

          <FuzzyDiagnostic status={status} />
        </div>
      )}

      {/* Disruption Event Log */}
      {disruptionLog.length > 0 && (
        <div className="card">
          <div className="card-title" style={{ marginBottom: '0.75rem' }}>Event Log</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            {disruptionLog.map((ev, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', padding: '0.5rem 0.75rem', background: '#0d131f', borderRadius: 6, fontSize: 12 }}>
                <span style={{ color: '#64748b', fontFamily: 'monospace' }}>{ev.time}</span>
                <span style={{ color: '#f8fafc', flex: 1 }}>{ev.type}</span>
                <span className="badge badge-rose">S={ev.severity?.toFixed(4)}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
