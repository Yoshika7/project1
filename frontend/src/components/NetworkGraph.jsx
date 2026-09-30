import React from 'react';

/**
 * Interactive SVG Network Visualization for AdaptIQ-R.
 * Renders nodes, edges, traffic congestion, blocked roads, and optimal routes.
 */
export default function NetworkGraph({
  scenario,
  currentRoute = [],
  detailedPath = [],
  onEdgeClick,
  onNodeClick,
  selectedEdge = null,
  width = 650,
  height = 550
}) {
  if (!scenario || !scenario.nodes) {
    return (
      <div style={{ display: 'flex', height: 400, alignItems: 'center', justifyContent: 'center', color: '#64748b' }}>
        No scenario loaded. Generate a network to begin.
      </div>
    );
  }

  // Padding & coordinate transformation (0-100 grid to SVG viewBox)
  const pad = 40;
  const innerW = width - pad * 2;
  const innerH = height - pad * 2;

  const toSvgX = (x) => pad + (x / 100.0) * innerW;
  const toSvgY = (y) => pad + (y / 100.0) * innerH;

  // Build lookup for quick node position access
  const nodeMap = scenario.nodes;

  // Active path coordinates
  const activePathNodes = detailedPath && detailedPath.length > 0 ? detailedPath : currentRoute;
  const pathPoints = activePathNodes
    .map((nid) => (nodeMap[nid] ? `${toSvgX(nodeMap[nid].x)},${toSvgY(nodeMap[nid].y)}` : null))
    .filter(Boolean)
    .join(' ');

  return (
    <div style={{ position: 'relative', background: '#0d131f', borderRadius: '0.75rem', overflow: 'hidden', border: '1px solid #1e293b' }}>
      <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`}>
        <defs>
          <linearGradient id="routeGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#06b6d4" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
          <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
            <feGaussianBlur stdDeviation="3" result="blur" />
            <feComposite in="SourceGraphic" in2="blur" operator="over" />
          </filter>
        </defs>

        {/* 1. Base Road Network Edges */}
        <g id="edges">
          {scenario.edges.map((edge, idx) => {
            const u = nodeMap[edge.source];
            const v = nodeMap[edge.target];
            if (!u || !v) return null;

            const isBlocked = edge.blocked;
            const isHighTraffic = edge.traffic_factor > 1.2;
            const isSelected = selectedEdge &&
              ((selectedEdge[0] === edge.source && selectedEdge[1] === edge.target) ||
               (selectedEdge[0] === edge.target && selectedEdge[1] === edge.source));

            let strokeColor = '#243049';
            let strokeWidth = 2;
            let strokeDash = 'none';

            if (isBlocked) {
              strokeColor = '#ef4444';
              strokeWidth = 3;
              strokeDash = '6,4';
            } else if (isHighTraffic) {
              strokeColor = '#f59e0b';
              strokeWidth = 2.8;
            } else if (isSelected) {
              strokeColor = '#38bdf8';
              strokeWidth = 3.5;
            }

            return (
              <g key={`edge-${idx}`} style={{ cursor: 'pointer' }} onClick={() => onEdgeClick && onEdgeClick(edge.source, edge.target)}>
                <line
                  x1={toSvgX(u.x)}
                  y1={toSvgY(u.y)}
                  x2={toSvgX(v.x)}
                  y2={toSvgY(v.y)}
                  stroke={strokeColor}
                  strokeWidth={strokeWidth}
                  strokeDasharray={strokeDash}
                  opacity={isBlocked ? 0.9 : 0.75}
                />
                {isBlocked && (
                  <circle
                    cx={(toSvgX(u.x) + toSvgX(v.x)) / 2}
                    cy={(toSvgY(u.y) + toSvgY(v.y)) / 2}
                    r={6}
                    fill="#ef4444"
                  />
                )}
              </g>
            );
          })}
        </g>

        {/* 2. Active Optimal Route Overlay */}
        {pathPoints && (
          <polyline
            points={pathPoints}
            fill="none"
            stroke="url(#routeGradient)"
            strokeWidth={3.5}
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="url(#glow)"
            opacity={0.9}
          />
        )}

        {/* 3. Nodes */}
        <g id="nodes">
          {Object.values(nodeMap).map((node) => {
            const cx = toSvgX(node.x);
            const cy = toSvgY(node.y);
            const isDepot = node.id === 0 || node.type === 'depot';
            const isPriority = node.type === 'priority';

            return (
              <g
                key={`node-${node.id}`}
                style={{ cursor: 'pointer' }}
                onClick={() => onNodeClick && onNodeClick(node.id)}
              >
                {/* Node halo */}
                <circle
                  cx={cx}
                  cy={cy}
                  r={isDepot ? 14 : isPriority ? 12 : 9}
                  fill={isDepot ? '#059669' : isPriority ? '#d97706' : '#1e293b'}
                  stroke={isDepot ? '#10b981' : isPriority ? '#f59e0b' : '#38bdf8'}
                  strokeWidth={2}
                />
                {/* Node ID text */}
                <text
                  x={cx}
                  y={cy + 4}
                  textAnchor="middle"
                  fill="#ffffff"
                  fontSize={isDepot ? 10 : 9}
                  fontWeight="bold"
                  pointerEvents="none"
                >
                  {isDepot ? 'D' : node.id}
                </text>
              </g>
            );
          })}
        </g>
      </svg>

      {/* Legend Overlay */}
      <div style={{
        position: 'absolute',
        bottom: 12,
        left: 12,
        background: 'rgba(15, 23, 42, 0.85)',
        backdropFilter: 'blur(6px)',
        padding: '8px 14px',
        borderRadius: '6px',
        border: '1px solid #1e293b',
        display: 'flex',
        gap: '16px',
        fontSize: '11px',
        color: '#94a3b8'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 10, height: 10, background: '#10b981', borderRadius: '50%' }}></span> Depot (0)
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 10, height: 10, background: '#f59e0b', borderRadius: '50%' }}></span> Priority Node
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 16, height: 2, background: '#06b6d4' }}></span> Best Route
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <span style={{ width: 16, height: 2, background: '#ef4444', borderTop: '2px dashed #ef4444' }}></span> Blocked Road
        </div>
      </div>
    </div>
  );
}
