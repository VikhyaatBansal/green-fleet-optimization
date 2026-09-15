import json
import os
import numpy as np
import pandas as pd

def generate_dataset(num_records=4000, seed=42):
    np.random.seed(seed)
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(current_dir, 'vessels.json'), 'r') as f:
        vessels = json.load(f)
    with open(os.path.join(current_dir, 'fuels.json'), 'r') as f:
        fuels = {f['fuel_id']: f for f in json.load(f)}

    vessel_dict = {v['vessel_id']: v for v in vessels}
    vessel_ids = list(vessel_dict.keys())
    
    records = []
    
    # Physics calibration constant k to align kW * g/kWh * hr to metric tonnes
    SPEED_REF = 14.0
    K_PHYSICS = 1.0 / 1_000_000.0  # converts kW * g/kWh * hr to tonnes

    for i in range(1, num_records + 1):
        trip_id = f"TRIP-{i:04d}"
        v_id = np.random.choice(vessel_ids)
        v = vessel_dict[v_id]
        
        # Select compatible fuel
        compat_fuels = v['compatible_fuels']
        fuel_id = np.random.choice(compat_fuels)
        fuel_meta = fuels[fuel_id]
        
        # Operational variables
        min_spd = v['min_speed_kn']
        max_spd = v['max_speed_kn']
        speed_kn = round(float(np.random.uniform(min_spd, max_spd)), 2)
        
        # Cargo load: from 35% to 100% capacity
        max_cap = v['cargo_capacity_tonnes']
        cargo_load_tonnes = round(float(np.random.uniform(0.35 * max_cap, max_cap)), 1)
        cargo_load_ratio = round(cargo_load_tonnes / max_cap, 4)
        
        # Distance (nm): 500 to 4200 nm
        distance_nm = round(float(np.random.uniform(500, 4200)), 1)
        voyage_duration_hr = round(distance_nm / speed_kn, 2)
        
        # Sea state (Douglas scale 1-7)
        sea_state_douglas = int(np.random.choice([1, 2, 3, 4, 5, 6, 7], p=[0.10, 0.25, 0.30, 0.20, 0.10, 0.04, 0.01]))
        wave_height_m = round(float(np.random.uniform(0.3 * sea_state_douglas, 0.9 * sea_state_douglas)), 2)
        wind_speed_kn = round(float(np.random.uniform(4 * sea_state_douglas, 7 * sea_state_douglas + 5)), 1)
        
        # Weather resistance multiplier: hydrodynamic resistance escalates with wave & wind
        weather_multiplier = 1.0 + (0.025 * (sea_state_douglas - 1)) + (0.0015 * wind_speed_kn)
        
        # Load factor: displacement effect on wetted surface resistance
        displacement_ratio = (0.25 * v['DWT'] + cargo_load_tonnes) / (1.25 * v['DWT'])
        load_factor = 0.70 + 0.30 * displacement_ratio
        
        engine_power_kw = v['engine_power_kw']
        sfoc_g_per_kwh = v['SFOC_g_per_kwh']
        energy_density_rel = fuel_meta['energy_density_relative']
        
        # Base physics calculation
        speed_ratio_cubed = (speed_kn / SPEED_REF) ** 3
        power_effective_kw = engine_power_kw * 0.75 * speed_ratio_cubed * load_factor
        base_fuel_tonnes = (power_effective_kw * sfoc_g_per_kwh * voyage_duration_hr * K_PHYSICS) / energy_density_rel
        
        # Real-world non-linear effects
        aux_power_kw = 0.08 * engine_power_kw + float(np.random.uniform(50, 150))
        aux_fuel_tonnes = (aux_power_kw * 195.0 * voyage_duration_hr * K_PHYSICS) / energy_density_rel
        
        age_years = 2026 - v['built_year']
        fouling_penalty = 1.0 + 0.008 * age_years
        
        noise = float(np.random.normal(0, 0.025))
        
        actual_fuel_tonnes = (base_fuel_tonnes * weather_multiplier * fouling_penalty + aux_fuel_tonnes) * (1.0 + noise)
        actual_fuel_tonnes = round(max(0.5, actual_fuel_tonnes), 3)
        base_fuel_tonnes = round(base_fuel_tonnes, 3)
        residual_tonnes = round(actual_fuel_tonnes - base_fuel_tonnes, 3)
        
        shore_power_available = int(np.random.choice([0, 1], p=[0.45, 0.55]))
        
        fuel_price = fuel_meta['cost_per_tonne_usd']
        bunker_cost = actual_fuel_tonnes * fuel_price
        port_fee = 12500.0 + (0.15 * v['DWT'])
        shore_power_credit = 4500.0 if shore_power_available else 0.0
        voyage_cost_usd = round(bunker_cost + port_fee - shore_power_credit, 2)
        
        emissions_co2e_tonnes = round(actual_fuel_tonnes * fuel_meta['emission_factor_co2e_per_tonne'], 3)
        
        records.append({
            'trip_id': trip_id,
            'vessel_id': v_id,
            'vessel_type': v['type'],
            'dwt_tonnes': v['DWT'],
            'cargo_capacity_tonnes': v['cargo_capacity_tonnes'],
            'engine_power_kw': v['engine_power_kw'],
            'sfoc_baseline_g_kwh': v['SFOC_g_per_kwh'],
            'fuel_type': fuel_id,
            'fuel_energy_density_relative': energy_density_rel,
            'fuel_cost_per_tonne_usd': fuel_price,
            'emission_factor_wtw_relative': fuel_meta['emission_factor_wtw_relative'],
            'distance_nm': distance_nm,
            'speed_kn': speed_kn,
            'cargo_load_tonnes': cargo_load_tonnes,
            'cargo_load_ratio': cargo_load_ratio,
            'sea_state_douglas': sea_state_douglas,
            'wave_height_m': wave_height_m,
            'wind_speed_kn': wind_speed_kn,
            'weather_resistance_factor': round(weather_multiplier, 4),
            'voyage_duration_hr': voyage_duration_hr,
            'physics_base_fuel_tonnes': base_fuel_tonnes,
            'engine_efficiency_degradation': round(fouling_penalty, 4),
            'auxiliary_power_kw': round(aux_power_kw, 1),
            'shore_power_available': shore_power_available,
            'fuel_consumed_tonnes': actual_fuel_tonnes,
            'fuel_residual_tonnes': residual_tonnes,
            'voyage_cost_usd': voyage_cost_usd,
            'ghg_emissions_co2e_tonnes': emissions_co2e_tonnes
        })

    df = pd.DataFrame(records)
    output_path = os.path.join(current_dir, 'synthetic_trips.csv')
    df.to_csv(output_path, index=False)
    print(f"Generated {len(df)} synthetic trip records at: {output_path}")
    print(f"Columns ({len(df.columns)}): {list(df.columns)}")

if __name__ == '__main__':
    generate_dataset()
