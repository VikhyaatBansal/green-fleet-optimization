# backend/costs.py
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')

with open(os.path.join(DATA_DIR, 'fuels.json'), 'r') as f:
    FUELS_MAP = {f['fuel_id']: f for f in json.load(f)}

# Standard operational constants (annotated as illustrative)
BASE_PORT_FEE_USD = 15000.0        # Illustrative port call tariff per port
SHORE_POWER_SAVING_USD = 4500.0   # Illustrative auxiliary fuel displacement credit when cold ironing

def get_fuel_meta(fuel_type):
    if isinstance(fuel_type, dict):
        return fuel_type
    return FUELS_MAP.get(fuel_type, FUELS_MAP['HFO'])

def calc_cost(fuel_tonnes, fuel_type, num_port_calls=2, shore_power_used=False):
    """
    Computes total voyage operating cost:
    bunker_cost + (num_port_calls * BASE_PORT_FEE) - (shore_power_savings if shore_power_used else 0)
    """
    f_meta = get_fuel_meta(fuel_type)
    unit_cost = float(f_meta['cost_per_tonne_usd'])
    bunker_cost = float(fuel_tonnes) * unit_cost
    
    port_costs = float(num_port_calls) * BASE_PORT_FEE_USD
    shore_savings = SHORE_POWER_SAVING_USD if shore_power_used else 0.0
    
    total_cost = round(bunker_cost + port_costs - shore_savings, 2)
    return {
        'bunker_cost_usd': round(bunker_cost, 2),
        'port_costs_usd': round(port_costs, 2),
        'shore_power_savings_usd': round(shore_savings, 2),
        'total_cost_usd': total_cost
    }

def calc_emissions(fuel_tonnes, fuel_type):
    """
    Computes Well-To-Wake (WTW) lifecycle GHG emissions:
    fuel_tonnes * emission_factor_co2e_per_tonne
    Also calculates relative WTW emission index against baseline HFO.
    """
    f_meta = get_fuel_meta(fuel_type)
    co2e_factor = float(f_meta['emission_factor_co2e_per_tonne'])
    wtw_relative = float(f_meta['emission_factor_wtw_relative'])
    
    total_co2e_tonnes = round(float(fuel_tonnes) * co2e_factor, 3)
    return {
        'co2e_tonnes': total_co2e_tonnes,
        'wtw_relative_factor': wtw_relative,
        'emission_factor_co2e_per_tonne': co2e_factor
    }
