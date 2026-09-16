// frontend/src/lib/api.ts
const API_BASE = process.env.NEXT_PUBLIC_API_URL;

if (!API_BASE) {
  throw new Error('NEXT_PUBLIC_API_URL is working fine');
}

export interface Vessel {
  vessel_id: string;
  name: string;
  type: string;
  DWT: number;
  cargo_capacity_tonnes: number;
  engine_power_kw: number;
  SFOC_g_per_kwh: number;
  max_speed_kn: number;
  min_speed_kn: number;
  compatible_fuels: string[];
  built_year: number;
}

export interface Fuel {
  fuel_id: string;
  name: string;
  energy_density_relative: number;
  energy_density_mj_per_kg: number;
  cost_per_tonne_usd: number;
  emission_factor_wtw_relative: number;
  emission_factor_co2e_per_tonne: number;
  vessel_compatible_types: string[];
  illustrative: boolean;
  notes: string;
}

export interface RouteItem {
  route_id: string;
  origin: string;
  destination: string;
  distance_nm: number;
  typical_sea_state: number;
}

export interface MLMetrics {
  model_name: string;
  train_samples: number;
  test_samples: number;
  features: string[];
  hybrid_metrics: {
    mae_tonnes: number;
    rmse_tonnes: number;
    r2_score: number;
  };
  baseline_only_metrics: {
    mae_tonnes: number;
    rmse_tonnes: number;
    r2_score: number;
  };
  improvement: {
    mae_reduction_pct: number;
    rmse_reduction_pct: number;
  };
}

export interface PlanDetails {
  vessel_id: string;
  vessel_name: string;
  vessel_type: string;
  fuel_type: string;
  fuel_name: string;
  speed_kn: number;
  shore_power_used: boolean;
  cargo_carried_tonnes: number;
  cargo_demand_tonnes: number;
  voyage_duration_hr: number;
  distance_nm: number;
  delay_hr: number;
}

export interface OptimizationResult {
  algorithm: string;
  algorithm_id: string;
  execution_time_ms: number;
  best_plan: PlanDetails;
  fuel_consumed_tonnes: number;
  cost_usd: number;
  emissions_co2e_tonnes: number;
  objective_score: number;
  feasible: boolean;
  penalties: number;
  infeasibility_reasons: string[];
  cost_breakdown: {
    bunker_cost_usd: number;
    port_costs_usd: number;
    shore_power_savings_usd: number;
    total_cost_usd: number;
  };
  emissions_breakdown: {
    co2e_tonnes: number;
    wtw_relative_factor: number;
    emission_factor_co2e_per_tonne: number;
  };
  convergence_history: number[];
}

export interface OptimizeRequestParams {
  algorithm: 'baseline' | 'classical' | 'quantum_inspired';
  cargo_demand_tonnes: number;
  deadline_hr: number;
  distance_nm?: number;
  sea_state?: number;
  weights?: {
    fuel: number;
    cost: number;
    emissions: number;
    delay: number;
  };
  pop_size?: number;
  generations?: number;
}

export interface FuelScenarioItem {
  fuel_id: string;
  fuel_name: string;
  fuel_consumed_tonnes: number;
  cost_usd: number;
  emissions_co2e_tonnes: number;
  best_vessel_id: string;
  speed_kn: number;
  shore_power_used: boolean;
  objective_score: number;
  feasible: boolean;
}

export interface BenchmarkStats {
  mean: number;
  std: number;
  min: number;
  max: number;
}

export interface BenchmarkAlgoResult {
  algorithm: string;
  algorithm_id: string;
  n_runs: number;
  objective_score: BenchmarkStats;
  fuel_consumed_tonnes: BenchmarkStats;
  cost_usd: BenchmarkStats;
  emissions_co2e_tonnes: BenchmarkStats;
  runtime_ms: BenchmarkStats;
  sample_plan: PlanDetails;
  convergence_history: number[];
  raw_scores?: number[];
}

export interface BenchmarkResponse {
  meta: {
    timestamp: string;
    n_runs: number;
    population_size: number;
    generations: number;
    quantum_mechanism: string;
    disclaimer: string;
  };
  comparison: {
    baseline: BenchmarkAlgoResult;
    classical_ga: BenchmarkAlgoResult;
    qiga: BenchmarkAlgoResult;
  };
}

async function handleFetch<T>(url: string, options?: RequestInit): Promise<T> {
  const res = await fetch(url, options);
  if (!res.ok) {
    const errorText = await res.text();
    throw new Error(`API Error [${res.status}]: ${errorText || res.statusText}`);
  }
  return res.json() as Promise<T>;
}

export async function fetchVessels(): Promise<Vessel[]> {
  return handleFetch<Vessel[]>(`${API_BASE}/vessels`);
}

export async function fetchFuels(): Promise<Fuel[]> {
  return handleFetch<Fuel[]>(`${API_BASE}/fuels`);
}

export async function fetchRoutes(): Promise<RouteItem[]> {
  return handleFetch<RouteItem[]>(`${API_BASE}/routes`);
}

export async function fetchMetrics(): Promise<MLMetrics> {
  return handleFetch<MLMetrics>(`${API_BASE}/metrics`);
}

export async function runOptimize(params: OptimizeRequestParams): Promise<OptimizationResult> {
  return handleFetch<OptimizationResult>(`${API_BASE}/optimize`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
}

export async function runFuelScenario(cargo_demand_tonnes: number = 45000.0, deadline_hr: number = 160.0): Promise<{ scenario_id: string; results: FuelScenarioItem[] }> {
  return handleFetch<{ scenario_id: string; results: FuelScenarioItem[] }>(`${API_BASE}/scenario`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      scenario_id: 'all_fuels_comparison',
      cargo_demand_tonnes,
      deadline_hr,
      distance_nm: 2200.0,
      sea_state: 3,
    }),
  });
}

export async function fetchBenchmark(force_rerun: boolean = false): Promise<BenchmarkResponse> {
  return handleFetch<BenchmarkResponse>(`${API_BASE}/benchmark`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ force_rerun }),
  });
}
