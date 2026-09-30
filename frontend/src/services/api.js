/**
 * AdaptIQ-R Backend API Client
 * Fully decouples frontend presentation from the CI Engine.
 */

const BASE_URL = '/api';

export async function generateScenario(nodeCount = 20, seed = 42) {
  const res = await fetch(`${BASE_URL}/scenario/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ node_count: Number(nodeCount), seed: Number(seed) })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getScenario(scenarioId) {
  const res = await fetch(`${BASE_URL}/scenario/${scenarioId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function startOptimization(params) {
  const res = await fetch(`${BASE_URL}/optimization/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getOptimizationStatus(runId) {
  const res = await fetch(`${BASE_URL}/optimization/${runId}/status`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getOptimizationHistory(runId) {
  const res = await fetch(`${BASE_URL}/optimization/${runId}/history`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function blockRoad(runId, source, target) {
  const res = await fetch(`${BASE_URL}/disruption/road-block`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, source: Number(source), target: Number(target) })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function surgeTraffic(runId, edges, factor = 2.5) {
  const res = await fetch(`${BASE_URL}/disruption/traffic-surge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, edges, factor: Number(factor) })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function changePriority(runId, nodeId, newPriority = 3) {
  const res = await fetch(`${BASE_URL}/disruption/priority-change`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, node_id: Number(nodeId), new_priority: Number(newPriority) })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function simulateVehicleFailure(runId, capacityLoss = 0.5) {
  const res = await fetch(`${BASE_URL}/disruption/vehicle-failure`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ run_id: runId, capacity_loss_fraction: Number(capacityLoss) })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function adaptOptimization(runId, generations = 60) {
  const res = await fetch(`${BASE_URL}/optimization/${runId}/adapt`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ generations: Number(generations) })
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function runBenchmark(params) {
  const res = await fetch(`${BASE_URL}/benchmark/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export async function getBenchmark(benchmarkId) {
  const res = await fetch(`${BASE_URL}/benchmark/${benchmarkId}`);
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}
