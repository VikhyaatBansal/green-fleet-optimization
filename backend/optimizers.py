# backend/optimizers.py
import os
import sys
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
import json
import time
import math
import numpy as np
from backend.prediction import predict_fuel, get_vessel_obj, get_fuel_obj, VESSELS_DATA, FUELS_DATA
from backend.costs import calc_cost, calc_emissions

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

with open(os.path.join(DATA_DIR, 'vessels.json'), 'r') as f:
    DEFAULT_VESSELS = json.load(f)

with open(os.path.join(DATA_DIR, 'fuels.json'), 'r') as f:
    DEFAULT_FUELS = json.load(f)

DEFAULT_ROUTE = {
    'route_id': 'ROTTERDAM-SINGAPORE-LEG1',
    'origin': 'Rotterdam',
    'destination': 'Gibraltar / Suez Access',
    'distance_nm': 2200.0,
    'typical_sea_state': 3
}

def evaluate_plan(plan, cargo_demand=45000.0, deadline_hr=160.0, weights=None, distance_nm=2200.0, sea_state=3):
    """
    Evaluates a candidate maritime plan:
    plan = {
        'vessel_id': str,
        'fuel_type': str,
        'speed_kn': float,
        'shore_power_used': bool
    }
    """
    if weights is None:
        weights = {'fuel': 0.35, 'cost': 0.35, 'emissions': 0.30, 'delay': 1.0}
        
    v = get_vessel_obj(plan['vessel_id'])
    f = get_fuel_obj(plan['fuel_type'])
    
    speed_kn = float(plan['speed_kn'])
    shore_power = bool(plan.get('shore_power_used', False))
    
    # 1. Physical limits & feasibility checks
    penalties = 0.0
    feasible = True
    infeasibility_reasons = []
    
    # Fuel compatibility
    if f['fuel_id'] not in v['compatible_fuels']:
        feasible = False
        penalties += 150.0
        infeasibility_reasons.append(f"Fuel {f['fuel_id']} incompatible with vessel {v['vessel_id']}")
        
    # Speed bounds
    if speed_kn < v['min_speed_kn'] - 0.01 or speed_kn > v['max_speed_kn'] + 0.01:
        feasible = False
        penalties += 80.0 + 10.0 * abs(speed_kn - v['max_speed_kn'])
        infeasibility_reasons.append(f"Speed {speed_kn} kn outside operating envelope [{v['min_speed_kn']}, {v['max_speed_kn']}]")
        
    # Cargo capacity
    carried_cargo = min(float(cargo_demand), float(v['cargo_capacity_tonnes']))
    if v['cargo_capacity_tonnes'] < cargo_demand:
        shortfall = cargo_demand - v['cargo_capacity_tonnes']
        # Heavy penalty for unmet cargo demand
        penalties += 100.0 + (shortfall / 1000.0) * 8.0
        feasible = False
        infeasibility_reasons.append(f"Capacity {v['cargo_capacity_tonnes']}t insufficient for demand {cargo_demand}t")
        
    # Voyage duration and delay
    voyage_duration_hr = round(distance_nm / speed_kn, 2)
    delay_hr = max(0.0, round(voyage_duration_hr - deadline_hr, 2))
    if delay_hr > 0.0:
        delay_penalty = (delay_hr / 10.0) ** 1.8
        penalties += delay_penalty * weights.get('delay', 1.0)
        feasible = False
        infeasibility_reasons.append(f"Deadline exceeded by {delay_hr:.1f} hours")
        
    # 2. Predicted consumption via hybrid ML model
    fuel_tonnes = predict_fuel(
        vessel=v,
        speed=speed_kn,
        cargo_load=carried_cargo,
        distance=distance_nm,
        fuel_type=f['fuel_id'],
        sea_state=sea_state
    )
    
    # 3. Financial costs
    cost_data = calc_cost(
        fuel_tonnes=fuel_tonnes,
        fuel_type=f['fuel_id'],
        num_port_calls=2,
        shore_power_used=shore_power
    )
    
    # 4. Emissions
    emiss_data = calc_emissions(
        fuel_tonnes=fuel_tonnes,
        fuel_type=f['fuel_id']
    )
    
    # 5. Multi-objective scalarized score (normalized)
    # Reference benchmarks: ~200t fuel, ~$180k cost, ~600t CO2e
    fuel_norm = fuel_tonnes / 150.0
    cost_norm = cost_data['total_cost_usd'] / 150000.0
    emiss_norm = emiss_data['co2e_tonnes'] / 500.0
    
    w_fuel = float(weights.get('fuel', 0.35))
    w_cost = float(weights.get('cost', 0.35))
    w_emiss = float(weights.get('emissions', 0.30))
    
    base_objective = (w_fuel * fuel_norm) + (w_cost * cost_norm) + (w_emiss * emiss_norm)
    objective_score = round(base_objective + penalties, 5)
    
    return {
        'plan': {
            'vessel_id': v['vessel_id'],
            'vessel_name': v['name'],
            'vessel_type': v['type'],
            'fuel_type': f['fuel_id'],
            'fuel_name': f['name'],
            'speed_kn': round(speed_kn, 2),
            'shore_power_used': shore_power,
            'cargo_carried_tonnes': carried_cargo,
            'cargo_demand_tonnes': cargo_demand,
            'voyage_duration_hr': voyage_duration_hr,
            'distance_nm': distance_nm,
            'delay_hr': delay_hr
        },
        'fuel_consumed_tonnes': round(fuel_tonnes, 3),
        'cost_breakdown': cost_data,
        'emissions_breakdown': emiss_data,
        'objective_score': objective_score,
        'feasible': feasible,
        'penalties': round(penalties, 3),
        'infeasibility_reasons': infeasibility_reasons
    }

def decode_bits(bits, vessels, fuels):
    """
    Decodes an 11-bit chromosome into a concrete candidate plan:
    - bits[0..2]: vessel index (3 bits mod N_vessels)
    - bits[3..5]: fuel index (3 bits mod N_fuels)
    - bits[6..9]: speed index (4 bits -> 16 speed intervals)
    - bits[10]: shore power flag (1 bit -> bool)
    """
    v_idx = (bits[0] * 4 + bits[1] * 2 + bits[2]) % len(vessels)
    vessel = vessels[v_idx]
    
    f_idx = (bits[3] * 4 + bits[4] * 2 + bits[5]) % len(fuels)
    fuel = fuels[f_idx]
    
    speed_raw = bits[6] * 8 + bits[7] * 4 + bits[8] * 2 + bits[9]
    spd_ratio = speed_raw / 15.0
    min_spd = vessel['min_speed_kn']
    max_spd = vessel['max_speed_kn']
    speed_kn = min_spd + spd_ratio * (max_spd - min_spd)
    
    shore_power = bool(bits[10] == 1)
    
    return {
        'vessel_id': vessel['vessel_id'],
        'fuel_type': fuel['fuel_id'],
        'speed_kn': round(speed_kn, 2),
        'shore_power_used': shore_power
    }

def encode_plan_to_bits(plan, vessels, fuels):
    """Encodes a plan into an 11-bit array."""
    v_ids = [v['vessel_id'] for v in vessels]
    v_idx = v_ids.index(plan['vessel_id']) if plan['vessel_id'] in v_ids else 0
    
    f_ids = [f['fuel_id'] for f in fuels]
    f_idx = f_ids.index(plan['fuel_type']) if plan['fuel_type'] in f_ids else 0
    
    v = vessels[v_idx]
    min_spd, max_spd = v['min_speed_kn'], v['max_speed_kn']
    ratio = max(0.0, min(1.0, (plan['speed_kn'] - min_spd) / (max_spd - min_spd)))
    spd_bin = int(round(ratio * 15))
    
    bits = [
        (v_idx >> 2) & 1, (v_idx >> 1) & 1, v_idx & 1,
        (f_idx >> 2) & 1, (f_idx >> 1) & 1, f_idx & 1,
        (spd_bin >> 3) & 1, (spd_bin >> 2) & 1, (spd_bin >> 1) & 1, spd_bin & 1,
        1 if plan.get('shore_power_used', False) else 0
    ]
    return bits

# Solver a) Baseline Rule-Based Solver
def baseline_solver(cargo_demand=45000.0, deadline_hr=160.0, weights=None, vessels=None, fuels=None, distance_nm=2200.0, sea_state=3):
    start_time = time.perf_counter()
    vessels = vessels or DEFAULT_VESSELS
    fuels = fuels or DEFAULT_FUELS
    
    # Deterministic rule:
    # 1. Smallest vessel with sufficient capacity
    sorted_vessels = sorted(vessels, key=lambda x: x['cargo_capacity_tonnes'])
    eligible = [v for v in sorted_vessels if v['cargo_capacity_tonnes'] >= cargo_demand]
    chosen_vessel = eligible[0] if eligible else sorted_vessels[-1]
    
    # 2. 80% of max speed
    chosen_speed = round(0.80 * chosen_vessel['max_speed_kn'], 2)
    # clamp to vessel range
    chosen_speed = max(chosen_vessel['min_speed_kn'], min(chosen_vessel['max_speed_kn'], chosen_speed))
    
    # 3. Cheapest compatible fuel
    compat_fuels = [f for f in fuels if f['fuel_id'] in chosen_vessel['compatible_fuels']]
    compat_fuels.sort(key=lambda x: x['cost_per_tonne_usd'])
    chosen_fuel = compat_fuels[0]['fuel_id'] if compat_fuels else 'HFO'
    
    # 4. No shore power
    shore_power = False
    
    plan = {
        'vessel_id': chosen_vessel['vessel_id'],
        'fuel_type': chosen_fuel,
        'speed_kn': chosen_speed,
        'shore_power_used': shore_power
    }
    
    eval_res = evaluate_plan(
        plan=plan,
        cargo_demand=cargo_demand,
        deadline_hr=deadline_hr,
        weights=weights,
        distance_nm=distance_nm,
        sea_state=sea_state
    )
    
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    
    return {
        'algorithm': 'Rule-Based Baseline',
        'algorithm_id': 'baseline',
        'execution_time_ms': elapsed_ms,
        'best_plan': eval_res['plan'],
        'fuel_consumed_tonnes': eval_res['fuel_consumed_tonnes'],
        'cost_usd': eval_res['cost_breakdown']['total_cost_usd'],
        'emissions_co2e_tonnes': eval_res['emissions_breakdown']['co2e_tonnes'],
        'objective_score': eval_res['objective_score'],
        'feasible': eval_res['feasible'],
        'penalties': eval_res['penalties'],
        'infeasibility_reasons': eval_res['infeasibility_reasons'],
        'cost_breakdown': eval_res['cost_breakdown'],
        'emissions_breakdown': eval_res['emissions_breakdown'],
        'convergence_history': [eval_res['objective_score']] * 60
    }

# Solver b) Classical Genetic Algorithm (GA)
def classical_ga_solver(cargo_demand=45000.0, deadline_hr=160.0, weights=None, vessels=None, fuels=None,
                        distance_nm=2200.0, sea_state=3, pop_size=40, generations=60, seed=None):
    start_time = time.perf_counter()
    if seed is not None:
        np.random.seed(seed)
        
    vessels = vessels or DEFAULT_VESSELS
    fuels = fuels or DEFAULT_FUELS
    N_BITS = 11
    
    # Random initial population of bitstrings
    pop = np.random.randint(0, 2, size=(pop_size, N_BITS)).tolist()
    
    convergence_history = []
    best_overall_res = None
    best_overall_bits = None
    
    for gen in range(generations):
        # Evaluate population
        evaluated = []
        for ind in pop:
            plan = decode_bits(ind, vessels, fuels)
            res = evaluate_plan(
                plan=plan,
                cargo_demand=cargo_demand,
                deadline_hr=deadline_hr,
                weights=weights,
                distance_nm=distance_nm,
                sea_state=sea_state
            )
            evaluated.append((res['objective_score'], ind, res))
            
        # Sort by objective (minimization)
        evaluated.sort(key=lambda x: x[0])
        gen_best_score, gen_best_bits, gen_best_res = evaluated[0]
        
        if best_overall_res is None or gen_best_score < best_overall_res['objective_score']:
            best_overall_res = gen_best_res
            best_overall_bits = gen_best_bits
            
        convergence_history.append(round(best_overall_res['objective_score'], 5))
        
        # Elitism: retain top 2
        next_pop = [evaluated[0][1].copy(), evaluated[1][1].copy()]
        
        # Tournament Selection + Crossover + Mutation
        while len(next_pop) < pop_size:
            # Tournament selection of 2 parents (tournament size = 3)
            def tournament():
                candidates = np.random.choice(len(evaluated), size=3, replace=False)
                winner_idx = min(candidates, key=lambda c: evaluated[c][0])
                return evaluated[winner_idx][1]
                
            p1 = tournament()
            p2 = tournament()
            
            # Two-point crossover
            if np.random.rand() < 0.85:
                pt1, pt2 = sorted(np.random.choice(N_BITS, size=2, replace=False))
                child1 = p1[:pt1] + p2[pt1:pt2] + p1[pt2:]
                child2 = p2[:pt1] + p1[pt1:pt2] + p2[pt2:]
            else:
                child1, child2 = p1.copy(), p2.copy()
                
            # Mutation (bit flip)
            for ch in [child1, child2]:
                for b in range(N_BITS):
                    if np.random.rand() < 0.05:
                        ch[b] = 1 - ch[b]
                if len(next_pop) < pop_size:
                    next_pop.append(ch)
                    
        pop = next_pop
        
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    
    return {
        'algorithm': 'Classical Genetic Algorithm',
        'algorithm_id': 'classical',
        'execution_time_ms': elapsed_ms,
        'best_plan': best_overall_res['plan'],
        'fuel_consumed_tonnes': best_overall_res['fuel_consumed_tonnes'],
        'cost_usd': best_overall_res['cost_breakdown']['total_cost_usd'],
        'emissions_co2e_tonnes': best_overall_res['emissions_breakdown']['co2e_tonnes'],
        'objective_score': best_overall_res['objective_score'],
        'feasible': best_overall_res['feasible'],
        'penalties': best_overall_res['penalties'],
        'infeasibility_reasons': best_overall_res['infeasibility_reasons'],
        'cost_breakdown': best_overall_res['cost_breakdown'],
        'emissions_breakdown': best_overall_res['emissions_breakdown'],
        'convergence_history': convergence_history
    }

# Solver c) Quantum-Inspired Genetic Algorithm (QIGA)
# Real Q-bit representation and rotation gate simulation
def qiga_solver(cargo_demand=45000.0, deadline_hr=160.0, weights=None, vessels=None, fuels=None,
                distance_nm=2200.0, sea_state=3, pop_size=40, generations=60, seed=None):
    start_time = time.perf_counter()
    if seed is not None:
        np.random.seed(seed)
        
    vessels = vessels or DEFAULT_VESSELS
    fuels = fuels or DEFAULT_FUELS
    N_BITS = 11
    
    # 1. Initialize Q-bit population
    # Each individual has N_BITS Q-bits, each represented by (alpha, beta)
    # alpha**2 + beta**2 = 1. Initially alpha = beta = 1/sqrt(2) (equal superposition)
    inv_sqrt2 = 1.0 / math.sqrt(2.0)
    q_pop_alpha = np.full((pop_size, N_BITS), inv_sqrt2, dtype=np.float64)
    q_pop_beta = np.full((pop_size, N_BITS), inv_sqrt2, dtype=np.float64)
    
    # Rotation angle magnitude delta_theta (0.025 * pi radians)
    DELTA_THETA = 0.025 * math.pi
    
    convergence_history = []
    b_best_score = float('inf')
    b_best_bits = None
    b_best_res = None
    
    for gen in range(generations):
        # 2. Quantum Measurement:
        # Sample classical bitstrings according to |beta|^2 probability of measuring '1'
        measured_bits = np.zeros((pop_size, N_BITS), dtype=int)
        gen_results = []
        
        for i in range(pop_size):
            for j in range(N_BITS):
                # Probability of bit being 1 is |beta|^2
                prob_1 = q_pop_beta[i, j] ** 2
                measured_bits[i, j] = 1 if np.random.rand() < prob_1 else 0
                
            candidate_bits = measured_bits[i].tolist()
            plan = decode_bits(candidate_bits, vessels, fuels)
            res = evaluate_plan(
                plan=plan,
                cargo_demand=cargo_demand,
                deadline_hr=deadline_hr,
                weights=weights,
                distance_nm=distance_nm,
                sea_state=sea_state
            )
            score = res['objective_score']
            gen_results.append((score, candidate_bits, res, i))
            
            if score < b_best_score:
                b_best_score = score
                b_best_bits = candidate_bits.copy()
                b_best_res = res
                
        convergence_history.append(round(b_best_score, 5))
        
        # 3. Quantum Rotation Gate Update:
        # Rotate (alpha, beta) amplitudes towards b_best bit values
        for i in range(pop_size):
            x_i = measured_bits[i]
            for j in range(N_BITS):
                target_bit = b_best_bits[j]
                current_bit = x_i[j]
                
                a = q_pop_alpha[i, j]
                b = q_pop_beta[i, j]
                
                # Direction of rotation
                # If target is 1 and measured is 0: rotate towards 1 (increase beta)
                # If target is 0 and measured is 1: rotate towards 0 (increase alpha)
                # If target == measured, slight reinforcement or no rotation
                if current_bit == 0 and target_bit == 1:
                    # Need to increase beta -> positive or negative theta depending on quadrant
                    theta = DELTA_THETA if (a * b) >= 0 else -DELTA_THETA
                elif current_bit == 1 and target_bit == 0:
                    # Need to increase alpha -> opposite direction
                    theta = -DELTA_THETA if (a * b) >= 0 else DELTA_THETA
                else:
                    # Reinforce target bit slightly
                    if target_bit == 1:
                        theta = 0.5 * DELTA_THETA if (a * b) >= 0 else -0.5 * DELTA_THETA
                    else:
                        theta = -0.5 * DELTA_THETA if (a * b) >= 0 else 0.5 * DELTA_THETA
                        
                # Rotation matrix: [cos(theta) -sin(theta); sin(theta) cos(theta)]
                cos_t = math.cos(theta)
                sin_t = math.sin(theta)
                
                new_a = a * cos_t - b * sin_t
                new_b = a * sin_t + b * cos_t
                
                # Normalize to ensure numerical precision alpha**2 + beta**2 == 1
                norm = math.sqrt(new_a**2 + new_b**2)
                q_pop_alpha[i, j] = new_a / norm
                q_pop_beta[i, j] = new_b / norm
                
    elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    
    return {
        'algorithm': 'Quantum-Inspired Genetic Algorithm (QIGA)',
        'algorithm_id': 'quantum_inspired',
        'execution_time_ms': elapsed_ms,
        'best_plan': b_best_res['plan'],
        'fuel_consumed_tonnes': b_best_res['fuel_consumed_tonnes'],
        'cost_usd': b_best_res['cost_breakdown']['total_cost_usd'],
        'emissions_co2e_tonnes': b_best_res['emissions_breakdown']['co2e_tonnes'],
        'objective_score': b_best_res['objective_score'],
        'feasible': b_best_res['feasible'],
        'penalties': b_best_res['penalties'],
        'infeasibility_reasons': b_best_res['infeasibility_reasons'],
        'cost_breakdown': b_best_res['cost_breakdown'],
        'emissions_breakdown': b_best_res['emissions_breakdown'],
        'convergence_history': convergence_history
    }
