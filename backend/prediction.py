# backend/prediction.py
import os
import json
import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import xgboost as xgb

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

# Load master vessels and fuels metadata
with open(os.path.join(DATA_DIR, 'vessels.json'), 'r') as f:
    VESSELS_DATA = {v['vessel_id']: v for v in json.load(f)}

with open(os.path.join(DATA_DIR, 'fuels.json'), 'r') as f:
    FUELS_DATA = {f['fuel_id']: f for f in json.load(f)}

SPEED_REF = 14.0
K_PHYSICS = 1.0 / 1_000_000.0

def get_vessel_obj(vessel):
    if isinstance(vessel, dict):
        return vessel
    return VESSELS_DATA.get(vessel, list(VESSELS_DATA.values())[0])

def get_fuel_obj(fuel):
    if isinstance(fuel, dict):
        return fuel
    return FUELS_DATA.get(fuel, FUELS_DATA['HFO'])

def physics_baseline(vessel, speed, cargo_load, distance, sea_state=3, fuel_type='HFO'):
    """
    Deterministic physics formula based on cubic speed-power law
    and displacement-dependent wetted surface resistance.
    """
    v = get_vessel_obj(vessel)
    f = get_fuel_obj(fuel_type)
    
    speed = float(max(1.0, speed))
    distance = float(max(1.0, distance))
    cargo_load = float(max(0.0, cargo_load))
    dwt = float(v['DWT'])
    engine_kw = float(v['engine_power_kw'])
    sfoc = float(v['SFOC_g_per_kwh'])
    energy_density = float(f.get('energy_density_relative', 1.0))
    
    voyage_duration_hr = distance / speed
    speed_ratio_cubed = (speed / SPEED_REF) ** 3
    
    # Displacement load factor
    displacement_ratio = (0.25 * dwt + cargo_load) / (1.25 * dwt)
    load_factor = 0.70 + 0.30 * displacement_ratio
    
    power_effective_kw = engine_kw * 0.75 * speed_ratio_cubed * load_factor
    base_fuel_tonnes = (power_effective_kw * sfoc * voyage_duration_hr * K_PHYSICS) / energy_density
    return float(max(0.1, round(base_fuel_tonnes, 4)))

FEATURE_COLS = [
    'engine_power_kw',
    'dwt_tonnes',
    'sfoc_baseline_g_kwh',
    'speed_kn',
    'cargo_load_tonnes',
    'cargo_load_ratio',
    'distance_nm',
    'sea_state_douglas',
    'wave_height_m',
    'wind_speed_kn',
    'fuel_energy_density_relative'
]

def train_and_save_model():
    os.makedirs(MODELS_DIR, exist_ok=True)
    csv_path = os.path.join(DATA_DIR, 'synthetic_trips.csv')
    df = pd.read_csv(csv_path)
    
    # Calculate baseline for each record to ensure exact parity
    df['computed_baseline'] = df.apply(
        lambda r: physics_baseline(
            r['vessel_id'], r['speed_kn'], r['cargo_load_tonnes'],
            r['distance_nm'], r['sea_state_douglas'], r['fuel_type']
        ),
        axis=1
    )
    
    # Residual = actual - physics_baseline
    df['residual_target'] = df['fuel_consumed_tonnes'] - df['computed_baseline']
    
    X = df[FEATURE_COLS]
    y = df['residual_target']
    
    X_train, X_test, y_train, y_test, df_train, df_test = train_test_split(
        X, y, df, test_size=0.20, random_state=42
    )
    
    regressor = xgb.XGBRegressor(
        n_estimators=160,
        max_depth=5,
        learning_rate=0.07,
        subsample=0.85,
        colsample_bytree=0.85,
        random_state=42
    )
    regressor.fit(X_train, y_train)
    
    # Predictions on test split
    residual_preds = regressor.predict(X_test)
    y_true_actual = df_test['fuel_consumed_tonnes'].values
    baseline_preds = df_test['computed_baseline'].values
    hybrid_preds = baseline_preds + residual_preds
    
    # Real computed test metrics
    hybrid_mae = float(mean_absolute_error(y_true_actual, hybrid_preds))
    hybrid_rmse = float(np.sqrt(mean_squared_error(y_true_actual, hybrid_preds)))
    hybrid_r2 = float(r2_score(y_true_actual, hybrid_preds))
    
    baseline_mae = float(mean_absolute_error(y_true_actual, baseline_preds))
    baseline_rmse = float(np.sqrt(mean_squared_error(y_true_actual, baseline_preds)))
    baseline_r2 = float(r2_score(y_true_actual, baseline_preds))
    
    metrics = {
        'model_name': 'Physics-Informed XGBoost Residual Regressor',
        'train_samples': len(X_train),
        'test_samples': len(X_test),
        'features': FEATURE_COLS,
        'hybrid_metrics': {
            'mae_tonnes': round(hybrid_mae, 4),
            'rmse_tonnes': round(hybrid_rmse, 4),
            'r2_score': round(hybrid_r2, 4)
        },
        'baseline_only_metrics': {
            'mae_tonnes': round(baseline_mae, 4),
            'rmse_tonnes': round(baseline_rmse, 4),
            'r2_score': round(baseline_r2, 4)
        },
        'improvement': {
            'mae_reduction_pct': round(((baseline_mae - hybrid_mae) / baseline_mae) * 100, 2),
            'rmse_reduction_pct': round(((baseline_rmse - hybrid_rmse) / baseline_rmse) * 100, 2)
        }
    }
    
    model_path = os.path.join(MODELS_DIR, 'fuel_correction_model.pkl')
    joblib.dump(regressor, model_path)
    
    metrics_path = os.path.join(MODELS_DIR, 'metrics.json')
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)
        
    print(f"Model successfully saved to: {model_path}")
    print(f"Metrics saved to: {metrics_path}")
    print(json.dumps(metrics, indent=2))
    return regressor, metrics

# Cached runtime model
_MODEL = None

def get_model():
    global _MODEL
    if _MODEL is None:
        model_path = os.path.join(MODELS_DIR, 'fuel_correction_model.pkl')
        if not os.path.exists(model_path):
            _MODEL, _ = train_and_save_model()
        else:
            _MODEL = joblib.load(model_path)
    return _MODEL

def predict_fuel(vessel, speed, cargo_load, distance, fuel_type='HFO', sea_state=3):
    """
    Hybrid predictor:
    fuel_tonnes = physics_baseline(...) + ml_residual_model.predict(features)
    """
    v = get_vessel_obj(vessel)
    f = get_fuel_obj(fuel_type)
    
    base_fuel = physics_baseline(v, speed, cargo_load, distance, sea_state, fuel_type)
    
    cargo_load_ratio = min(1.0, max(0.1, cargo_load / v['cargo_capacity_tonnes']))
    sea_state_clamped = max(1, min(7, int(sea_state)))
    approx_wave = 0.6 * sea_state_clamped
    approx_wind = 5.5 * sea_state_clamped + 2.0
    
    row = pd.DataFrame([{
        'engine_power_kw': float(v['engine_power_kw']),
        'dwt_tonnes': float(v['DWT']),
        'sfoc_baseline_g_kwh': float(v['SFOC_g_per_kwh']),
        'speed_kn': float(speed),
        'cargo_load_tonnes': float(cargo_load),
        'cargo_load_ratio': float(cargo_load_ratio),
        'distance_nm': float(distance),
        'sea_state_douglas': sea_state_clamped,
        'wave_height_m': approx_wave,
        'wind_speed_kn': approx_wind,
        'fuel_energy_density_relative': float(f['energy_density_relative'])
    }])[FEATURE_COLS]
    
    model = get_model()
    predicted_residual = float(model.predict(row)[0])
    
    total_fuel = max(0.1, round(base_fuel + predicted_residual, 3))
    return total_fuel

if __name__ == '__main__':
    train_and_save_model()
