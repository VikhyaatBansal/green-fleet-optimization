# backend/benchmark.py
import os
import sys
import json
import time
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.optimizers import baseline_solver, classical_ga_solver, qiga_solver

RESULTS_DIR = os.path.join(BASE_DIR, 'results')

def compute_stats(arr):
    arr = np.array(arr, dtype=float)
    return {
        'mean': round(float(np.mean(arr)), 4),
        'std': round(float(np.std(arr)), 4),
        'min': round(float(np.min(arr)), 4),
        'max': round(float(np.max(arr)), 4)
    }

def run_benchmark(n_runs=15, pop_size=40, generations=60):
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print(f"Starting Benchmark Suite: {n_runs} runs per stochastic optimizer (pop={pop_size}, gen={generations})...")
    
    # 1. Deterministic Baseline (1 run)
    base_res = baseline_solver()
    baseline_summary = {
        'algorithm': base_res['algorithm'],
        'algorithm_id': base_res['algorithm_id'],
        'n_runs': 1,
        'objective_score': {
            'mean': round(base_res['objective_score'], 4),
            'std': 0.0,
            'min': round(base_res['objective_score'], 4),
            'max': round(base_res['objective_score'], 4)
        },
        'fuel_consumed_tonnes': {
            'mean': round(base_res['fuel_consumed_tonnes'], 2),
            'std': 0.0,
            'min': round(base_res['fuel_consumed_tonnes'], 2),
            'max': round(base_res['fuel_consumed_tonnes'], 2)
        },
        'cost_usd': {
            'mean': round(base_res['cost_usd'], 2),
            'std': 0.0,
            'min': round(base_res['cost_usd'], 2),
            'max': round(base_res['cost_usd'], 2)
        },
        'emissions_co2e_tonnes': {
            'mean': round(base_res['emissions_co2e_tonnes'], 2),
            'std': 0.0,
            'min': round(base_res['emissions_co2e_tonnes'], 2),
            'max': round(base_res['emissions_co2e_tonnes'], 2)
        },
        'runtime_ms': {
            'mean': round(base_res['execution_time_ms'], 2),
            'std': 0.0,
            'min': round(base_res['execution_time_ms'], 2),
            'max': round(base_res['execution_time_ms'], 2)
        },
        'sample_plan': base_res['best_plan'],
        'convergence_history': base_res['convergence_history']
    }
    
    # 2. Classical GA runs
    ga_scores = []
    ga_fuels = []
    ga_costs = []
    ga_emissions = []
    ga_runtimes = []
    ga_histories = []
    best_ga_plan = None
    best_ga_score = float('inf')
    
    for seed in range(100, 100 + n_runs):
        res = classical_ga_solver(pop_size=pop_size, generations=generations, seed=seed)
        ga_scores.append(res['objective_score'])
        ga_fuels.append(res['fuel_consumed_tonnes'])
        ga_costs.append(res['cost_usd'])
        ga_emissions.append(res['emissions_co2e_tonnes'])
        ga_runtimes.append(res['execution_time_ms'])
        ga_histories.append(res['convergence_history'])
        if res['objective_score'] < best_ga_score:
            best_ga_score = res['objective_score']
            best_ga_plan = res['best_plan']
            
    ga_avg_conv = np.mean(ga_histories, axis=0).round(5).tolist()
    
    ga_summary = {
        'algorithm': 'Classical Genetic Algorithm',
        'algorithm_id': 'classical',
        'n_runs': n_runs,
        'objective_score': compute_stats(ga_scores),
        'fuel_consumed_tonnes': compute_stats(ga_fuels),
        'cost_usd': compute_stats(ga_costs),
        'emissions_co2e_tonnes': compute_stats(ga_emissions),
        'runtime_ms': compute_stats(ga_runtimes),
        'sample_plan': best_ga_plan,
        'convergence_history': ga_avg_conv,
        'raw_scores': [round(s, 4) for s in ga_scores]
    }
    
    # 3. Quantum-Inspired GA (QIGA) runs
    qiga_scores = []
    qiga_fuels = []
    qiga_costs = []
    qiga_emissions = []
    qiga_runtimes = []
    qiga_histories = []
    best_qiga_plan = None
    best_qiga_score = float('inf')
    
    for seed in range(200, 200 + n_runs):
        res = qiga_solver(pop_size=pop_size, generations=generations, seed=seed)
        qiga_scores.append(res['objective_score'])
        qiga_fuels.append(res['fuel_consumed_tonnes'])
        qiga_costs.append(res['cost_usd'])
        qiga_emissions.append(res['emissions_co2e_tonnes'])
        qiga_runtimes.append(res['execution_time_ms'])
        qiga_histories.append(res['convergence_history'])
        if res['objective_score'] < best_qiga_score:
            best_qiga_score = res['objective_score']
            best_qiga_plan = res['best_plan']
            
    qiga_avg_conv = np.mean(qiga_histories, axis=0).round(5).tolist()
    
    qiga_summary = {
        'algorithm': 'Quantum-Inspired Genetic Algorithm (QIGA)',
        'algorithm_id': 'quantum_inspired',
        'n_runs': n_runs,
        'objective_score': compute_stats(qiga_scores),
        'fuel_consumed_tonnes': compute_stats(qiga_fuels),
        'cost_usd': compute_stats(qiga_costs),
        'emissions_co2e_tonnes': compute_stats(qiga_emissions),
        'runtime_ms': compute_stats(qiga_runtimes),
        'sample_plan': best_qiga_plan,
        'convergence_history': qiga_avg_conv,
        'raw_scores': [round(s, 4) for s in qiga_scores]
    }
    
    results = {
        'meta': {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'n_runs': n_runs,
            'population_size': pop_size,
            'generations': generations,
            'quantum_mechanism': 'Classical simulation of Q-bit rotation via unitary rotation gates',
            'disclaimer': 'Synthetic physics-anchored dataset. Illustrative market prices.'
        },
        'comparison': {
            'baseline': baseline_summary,
            'classical_ga': ga_summary,
            'qiga': qiga_summary
        }
    }
    
    out_file = os.path.join(RESULTS_DIR, 'benchmark_results.json')
    with open(out_file, 'w') as f:
        json.dump(results, f, indent=2)
        
    print(f"Benchmark completed successfully! Results saved to: {out_file}")
    return results

if __name__ == '__main__':
    run_benchmark(n_runs=15, pop_size=40, generations=60)
