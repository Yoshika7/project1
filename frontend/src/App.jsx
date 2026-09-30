import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Navigation from './components/Navigation';
import Dashboard from './pages/Dashboard';
import ScenarioPage from './pages/ScenarioPage';
import OptimizationPage from './pages/OptimizationPage';
import DisruptionPage from './pages/DisruptionPage';
import ComparisonPage from './pages/ComparisonPage';
import AnalyticsPage from './pages/AnalyticsPage';
import BenchmarkPage from './pages/BenchmarkPage';

export default function App() {
  const [scenario, setScenario] = useState(null);
  const [runId, setRunId] = useState(null);

  return (
    <BrowserRouter>
      <div style={{ display: 'flex', minHeight: '100vh', background: '#080d16' }}>
        <Navigation />
        <main style={{ marginLeft: 220, flex: 1, padding: '2rem 2.5rem', maxWidth: 1400 }}>
          <Routes>
            <Route path="/" element={<Dashboard scenario={scenario} runId={runId} />} />
            <Route path="/scenario" element={<ScenarioPage scenario={scenario} setScenario={setScenario} />} />
            <Route path="/optimization" element={<OptimizationPage scenario={scenario} runId={runId} setRunId={setRunId} />} />
            <Route path="/disruption" element={<DisruptionPage scenario={scenario} runId={runId} />} />
            <Route path="/comparison" element={<ComparisonPage scenario={scenario} />} />
            <Route path="/analytics" element={<AnalyticsPage runId={runId} />} />
            <Route path="/benchmark" element={<BenchmarkPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
