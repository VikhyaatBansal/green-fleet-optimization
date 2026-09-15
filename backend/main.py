# backend/main.py
import os
import sys
import json
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.prediction import predict_fuel, physics_baseline, VESSELS_DATA, FUELS_DATA
from backend.costs import calc_cost, calc_emissions
from backend.optimizers import baseline_solver, classical_ga_solver, qiga_solver, DEFAULT_ROUTE
from backend.benchmark import run_benchmark

DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
RESULTS_DIR = os.path.join(BASE_DIR, 'results')

app = FastAPI(
    title="SIH 26138 Green Fleet Quantum-Inspired Optimizer API",
    description="Physics-informed predictive ML and Quantum-Inspired Genetic Algorithm (QIGA) for maritime decarbonization.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------- Pydantic Models -----------------

class PredictFuelRequest(BaseModel):
    vessel_id: str = Field(..., example="VESSEL-002")
    speed_kn: float = Field(..., example=14.0)
    cargo_load_tonnes: float = Field(..., example=45000.0)
    distance_nm: float = Field(2200.0, example=2200.0)
    fuel_type: str = Field("HFO", example="HFO")
    sea_state: int = Field(3, example=3, ge=1, le=7)

class PredictEmissionsRequest(BaseModel):
    fuel_tonnes: float = Field(..., example=150.0)
    fuel_type: str = Field("HFO", example="HFO")

class OptimizeRequest(BaseModel):
    algorithm: str = Field("quantum_inspired", example="quantum_inspired") # baseline | classical | quantum_inspired
    cargo_demand_tonnes: float = Field(45000.0, example=45000.0)
    deadline_hr: float = Field(160.0, example=160.0)
    distance_nm: float = Field(2200.0, example=2200.0)
    sea_state: int = Field(3, example=3, ge=1, le=7)
    weights: Optional[Dict[str, float]] = Field(
        default=None,
        example={"fuel": 0.35, "cost": 0.35, "emissions": 0.30, "delay": 1.0}
    )
    pop_size: Optional[int] = Field(35, example=35)
    generations: Optional[int] = Field(45, example=45)

class ScenarioRequest(BaseModel):
    scenario_id: str = Field(..., example="low_carbon") # "low_carbon" | "cost_priority" | "balanced" | "carbon_tax_strict" | "all_fuels_comparison"
    cargo_demand_tonnes: float = Field(45000.0, example=45000.0)
    deadline_hr: float = Field(160.0, example=160.0)
    distance_nm: float = Field(2200.0, example=2200.0)
    sea_state: int = Field(3, example=3)

class BenchmarkRequest(BaseModel):
    force_rerun: bool = Field(False, example=False)
    n_runs: Optional[int] = Field(5, example=5)

# ----------------- Routes -----------------

@app.get("/")
def read_root():
    return {
        "project": "SIH 26138 Green Fleet Optimization Prototype",
        "status": "online",
        "endpoints": [
            "/vessels", "/fuels", "/routes", "/metrics",
            "/predict/fuel", "/predict/emissions",
            "/optimize", "/scenario", "/benchmark"
        ],
        "disclaimer": "Synthetic physics-anchored dataset. Illustrative market prices. Classical simulation of quantum-inspired search."
    }

@app.get("/vessels")
def get_vessels():
    with open(os.path.join(DATA_DIR, 'vessels.json'), 'r') as f:
        return json.load(f)

@app.get("/fuels")
def get_fuels():
    with open(os.path.join(DATA_DIR, 'fuels.json'), 'r') as f:
        return json.load(f)

@app.get("/routes")
def get_routes():
    return [
        DEFAULT_ROUTE,
        {
            'route_id': 'SHANGHAI-LOSANGELES',
            'origin': 'Shanghai',
            'destination': 'Los Angeles',
            'distance_nm': 5250.0,
            'typical_sea_state': 4
        },
        {
            'route_id': 'SINGAPORE-ROTTERDAM-FULL',
            'origin': 'Singapore',
            'destination': 'Rotterdam',
            'distance_nm': 8280.0,
            'typical_sea_state': 3
        }
    ]

@app.get("/metrics")
def get_model_metrics():
    metrics_path = os.path.join(MODELS_DIR, 'metrics.json')
    if os.path.exists(metrics_path):
        with open(metrics_path, 'r') as f:
            return json.load(f)
    raise HTTPException(status_code=404, detail="Metrics file not found. Run model training first.")

@app.post("/predict/fuel")
def predict_fuel_endpoint(payload: PredictFuelRequest):
    if payload.vessel_id not in VESSELS_DATA:
        raise HTTPException(status_code=400, detail=f"Unknown vessel_id: {payload.vessel_id}")
    if payload.fuel_type not in FUELS_DATA:
        raise HTTPException(status_code=400, detail=f"Unknown fuel_type: {payload.fuel_type}")
        
    v = VESSELS_DATA[payload.vessel_id]
    base_tonnes = physics_baseline(
        vessel=v,
        speed=payload.speed_kn,
        cargo_load=payload.cargo_load_tonnes,
        distance=payload.distance_nm,
        sea_state=payload.sea_state,
        fuel_type=payload.fuel_type
    )
    predicted_tonnes = predict_fuel(
        vessel=v,
        speed=payload.speed_kn,
        cargo_load=payload.cargo_load_tonnes,
        distance=payload.distance_nm,
        fuel_type=payload.fuel_type,
        sea_state=payload.sea_state
    )
    ml_residual_correction = round(predicted_tonnes - base_tonnes, 3)
    
    return {
        "vessel_id": payload.vessel_id,
        "fuel_type": payload.fuel_type,
        "speed_kn": payload.speed_kn,
        "distance_nm": payload.distance_nm,
        "cargo_load_tonnes": payload.cargo_load_tonnes,
        "sea_state": payload.sea_state,
        "physics_base_fuel_tonnes": base_tonnes,
        "ml_residual_correction_tonnes": ml_residual_correction,
        "predicted_total_fuel_tonnes": predicted_tonnes
    }

@app.post("/predict/emissions")
def predict_emissions_endpoint(payload: PredictEmissionsRequest):
    if payload.fuel_type not in FUELS_DATA:
        raise HTTPException(status_code=400, detail=f"Unknown fuel_type: {payload.fuel_type}")
    res = calc_emissions(fuel_tonnes=payload.fuel_tonnes, fuel_type=payload.fuel_type)
    return {
        "fuel_tonnes": payload.fuel_tonnes,
        "fuel_type": payload.fuel_type,
        **res
    }

@app.post("/optimize")
def optimize_endpoint(payload: OptimizeRequest):
    algo = payload.algorithm.lower()
    weights = payload.weights or {'fuel': 0.35, 'cost': 0.35, 'emissions': 0.30, 'delay': 1.0}
    pop_size = payload.pop_size or 35
    generations = payload.generations or 45
    
    if algo == "baseline":
        result = baseline_solver(
            cargo_demand=payload.cargo_demand_tonnes,
            deadline_hr=payload.deadline_hr,
            weights=weights,
            distance_nm=payload.distance_nm,
            sea_state=payload.sea_state
        )
    elif algo in ["classical", "ga", "classical_ga"]:
        result = classical_ga_solver(
            cargo_demand=payload.cargo_demand_tonnes,
            deadline_hr=payload.deadline_hr,
            weights=weights,
            distance_nm=payload.distance_nm,
            sea_state=payload.sea_state,
            pop_size=pop_size,
            generations=generations
        )
    elif algo in ["quantum_inspired", "qiga", "quantum"]:
        result = qiga_solver(
            cargo_demand=payload.cargo_demand_tonnes,
            deadline_hr=payload.deadline_hr,
            weights=weights,
            distance_nm=payload.distance_nm,
            sea_state=payload.sea_state,
            pop_size=pop_size,
            generations=generations
        )
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported algorithm '{payload.algorithm}'. Choose 'baseline', 'classical', or 'quantum_inspired'."
        )
        
    return result

@app.post("/scenario")
def scenario_endpoint(payload: ScenarioRequest):
    sc_id = payload.scenario_id.lower()
    
    # Pre-configured scenario weighting
    if sc_id == "low_carbon":
        weights = {"fuel": 0.15, "cost": 0.15, "emissions": 0.70, "delay": 1.2}
    elif sc_id == "cost_priority":
        weights = {"fuel": 0.30, "cost": 0.60, "emissions": 0.10, "delay": 1.0}
    elif sc_id == "balanced":
        weights = {"fuel": 0.35, "cost": 0.35, "emissions": 0.30, "delay": 1.0}
    elif sc_id == "carbon_tax_strict":
        # Simulates strict IMO/EU-ETS carbon penalty
        weights = {"fuel": 0.10, "cost": 0.10, "emissions": 0.80, "delay": 1.5}
    elif sc_id == "all_fuels_comparison":
        # Run comparison forcing each fuel type
        all_fuels = ["HFO", "LNG", "Methanol", "Ammonia", "Hydrogen"]
        fuel_results = []
        for f_id in all_fuels:
            # Filter vessels compatible with this fuel
            compat_vessels = [v for v in VESSELS_DATA.values() if f_id in v['compatible_fuels']]
            if not compat_vessels:
                continue
            # Single-fuel optimization using QIGA
            res = qiga_solver(
                cargo_demand=payload.cargo_demand_tonnes,
                deadline_hr=payload.deadline_hr,
                weights={"fuel": 0.30, "cost": 0.40, "emissions": 0.30, "delay": 1.0},
                vessels=compat_vessels,
                fuels=[FUELS_DATA[f_id]],
                distance_nm=payload.distance_nm,
                sea_state=payload.sea_state,
                pop_size=25,
                generations=30
            )
            fuel_results.append({
                "fuel_id": f_id,
                "fuel_name": FUELS_DATA[f_id]["name"],
                "fuel_consumed_tonnes": res["fuel_consumed_tonnes"],
                "cost_usd": res["cost_usd"],
                "emissions_co2e_tonnes": res["emissions_co2e_tonnes"],
                "best_vessel_id": res["best_plan"]["vessel_id"],
                "speed_kn": res["best_plan"]["speed_kn"],
                "shore_power_used": res["best_plan"]["shore_power_used"],
                "objective_score": res["objective_score"],
                "feasible": res["feasible"]
            })
        return {
            "scenario_id": "all_fuels_comparison",
            "results": fuel_results
        }
    else:
        weights = {"fuel": 0.35, "cost": 0.35, "emissions": 0.30, "delay": 1.0}
        
    res = qiga_solver(
        cargo_demand=payload.cargo_demand_tonnes,
        deadline_hr=payload.deadline_hr,
        weights=weights,
        distance_nm=payload.distance_nm,
        sea_state=payload.sea_state,
        pop_size=35,
        generations=45
    )
    return {
        "scenario_id": sc_id,
        "weights_applied": weights,
        "optimization_result": res
    }

@app.post("/benchmark")
def benchmark_endpoint(payload: BenchmarkRequest = Body(default_factory=BenchmarkRequest)):
    bench_file = os.path.join(RESULTS_DIR, 'benchmark_results.json')
    if payload.force_rerun or not os.path.exists(bench_file):
        n_runs = payload.n_runs or 5
        res = run_benchmark(n_runs=n_runs, pop_size=35, generations=45)
        return res
        
    with open(bench_file, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
