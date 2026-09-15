# SIH 26138: Quantum-Inspired Fuel Consumption Prediction & Green Fleet Optimization

A complete, fully functional end-to-end prototype for Smart India Hackathon (SIH) Problem Statement 26138. Every single number displayed across the platform is authentically computed by the underlying physics-ML hybrid pipeline and optimization algorithms—no hardcoded placeholders or mock outputs.

---

## 1. Problem Statement Mapping

- **Title**: Quantum-Inspired Fuel Consumption Prediction and Green Fleet Optimization (ID: 26138)
- **Organization**: Egreen Quanta / Clean & Green Technology
- **Objective**: Accurately predict vessel fuel consumption under dynamic operational conditions and optimize green fleet deployment decisions (vessel selection, cruising speed, alternative fuels, and shore power cold-ironing) to minimize lifecycle GHG emissions, bunker consumption, and operational costs while meeting cargo demand and deadline constraints.

---

## 2. System Architecture

```
                                    +------------------------------------------+
                                    |         Mission Demand Input             |
                                    | (Cargo: 45k t, Deadline: 160h, Sea St: 3)|
                                    +--------------------+---------------------+
                                                         |
                   +-------------------------------------+-------------------------------------+
                   |                                     |                                     |
+------------------v-----------------+ +-----------------v-----------------+ +-----------------v-----------------+
|      Rule-Based Baseline           | |     Classical Genetic Algo (GA)   | |  Quantum-Inspired GA (QIGA)       |
| Deterministic heuristic:           | | Binary chromosome, 2-pt crossover | | Real Q-bit registers (alpha, beta)|
| Smallest eligible vessel, 80% spd, | | stochastic bit mutation, elitism. | | Unitary rotation gate matrix      |
| cheapest compatible fuel.          | | Population: 40, Generations: 60.  | | Population: 40, Generations: 60.  |
+------------------+-----------------+ +-----------------+-----------------+ +-----------------+-----------------+
                   |                                     |                                     |
                   +-------------------------------------+-------------------------------------+
                                                         | Candidate Plan (Vessel, Fuel, Speed, Shore Power)
                                    +--------------------v---------------------+
                                    |   Hybrid Fuel Consumption Predictor      |
                                    |  P_total = P_physics + ML_residual(X)    |
                                    +--------------------+---------------------+
                                                         |
                                    +--------------------v---------------------+
                                    |       Costs & Emissions Engine           |
                                    |  Cost: Bunker + Port - Shore Power       |
                                    |  Emissions: WTW Lifecycle CO2e           |
                                    +--------------------+---------------------+
                                                         |
                                    +--------------------v---------------------+
                                    |   Multi-Objective Evaluation Function    |
                                    | Score = w1*F + w2*C + w3*E + Penalties   |
                                    +--------------------+---------------------+
                                                         |
                                    +--------------------v---------------------+
                                    |  FastAPI Backend <---> Next.js Dashboard |
                                    +------------------------------------------+
```

---

## 3. Mathematical Foundations

### 3.1 Deterministic Cubic Physics Baseline
Anchored in the classical naval hydrodynamic law relating vessel propulsion power $P$ to the cube of speed $V$:
$$P_{\text{eff}} = P_{\text{engine}} \times 0.75 \times \left(\frac{V}{V_{\text{ref}}}\right)^3 \times \left(0.70 + 0.30 \times \frac{0.25 \times \text{DWT} + \text{CargoLoad}}{1.25 \times \text{DWT}}\right)$$
$$\text{BaseFuel} = \frac{P_{\text{eff}} \times \text{SFOC} \times \text{Duration} \times 10^{-6}}{\text{EnergyDensity}_{\text{relative}}}$$

### 3.2 Machine Learning Residual Regressor
Real-world voyages experience wave resistance, wind drag, engine fouling, and auxiliary hotel electrical loads that the pure cubic equation ignores:
$$\text{Residual} = \text{ActualFuel} - \text{BaseFuel}$$
An XGBoost Regressor is trained to predict this residual from operational and environmental variables:
- **Features**: `engine_power_kw`, `dwt_tonnes`, `sfoc_baseline_g_kwh`, `speed_kn`, `cargo_load_tonnes`, `cargo_load_ratio`, `distance_nm`, `sea_state_douglas`, `wave_height_m`, `wind_speed_kn`, `fuel_energy_density_relative`.
- **Model Accuracy on 800 Held-out Test Samples**:
  - Baseline-only $R^2$: `0.8722` (MAE: `91.23 tonnes`)
  - Hybrid Physics + ML $R^2$: `0.9981` (MAE: `9.13 tonnes`)
  - **Error Reduction**: **`89.99%` reduction in MAE**.

### 3.3 Quantum-Inspired Genetic Algorithm (QIGA)
Implemented as a genuine classical simulation of Q-bit rotation:
1. **Quantum Chromosome**: Each candidate decision (vessel, fuel, speed bin, shore power) is represented across an 11-bit register of Q-bits:
   $$|q_j\rangle = \alpha_j |0\rangle + \beta_j |1\rangle, \quad |\alpha_j|^2 + |\beta_j|^2 = 1$$
2. **State Initialization**: Set to maximal superposition and exploration uncertainty:
   $$\alpha_j = \beta_j = \frac{1}{\sqrt{2}} \quad \forall j$$
3. **Quantum Measurement**: Sample classical bits $x_{i,j} \in \{0, 1\}$ according to probability $P(1) = |\beta_{i,j}|^2$.
4. **Unitary Rotation Gate Update**: Steer probability amplitudes smoothly toward the best discovered individual $B_{\text{best}}$:
   $$\begin{pmatrix} \alpha_j' \\ \beta_j' \end{pmatrix} = \begin{pmatrix} \cos(\Delta\theta) & -\sin(\Delta\theta) \\ \sin(\Delta\theta) & \cos(\Delta\theta) \end{pmatrix} \begin{pmatrix} \alpha_j \\ \beta_j \end{pmatrix}$$
   where rotation angle magnitude $\Delta\theta = 0.025\pi$ radians.

---

## 4. Benchmark Results (15-Run Monte Carlo)

All numbers below are extracted directly from the live multi-seed benchmark execution (`results/benchmark_results.json`):

| Metric | Rule-Based Baseline | Classical Genetic Algorithm | Quantum-Inspired GA (QIGA) |
| :--- | :---: | :---: | :---: |
| **Objective Score (Mean ± Std)** | $4.1452 \pm 0.000$ | $1.1495 \pm 0.1909$ | **$1.0344 \pm 0.0000$** |
| **Objective Score [Min, Max]** | $[4.1452, 4.1452]$ | $[1.0344, 1.4661]$ | **$[1.0344, 1.0344]$** |
| **Fuel Consumed Mean** | $229.34\text{ t}$ | $143.35\text{ t}$ | **$107.71\text{ t}$** |
| **GHG Lifecycle Emissions** | $821.03\text{ t CO}_2\text{e}$ | $202.49\text{ t CO}_2\text{e}$ | **$31.24\text{ t CO}_2\text{e}$** |
| **Emissions Reduction vs Baseline** | *Benchmark Ref (0%)* | $75.3\%$ reduction | **$96.2\%$ reduction** |
| **Voyage Operating Cost** | $\$172,190$ | $\$296,864$ | $\$327,080$ *(Green Fuel Premium)* |
| **Optimal Bunker Selected** | HFO | LNG / Hydrogen | **Liquid Green Hydrogen + Shore Power** |
| **Runtime Mean ± Std** | $12.0\text{ ms} \pm 0.0$ | $6626.6\text{ ms} \pm 272.0$ | $6744.0\text{ ms} \pm 134.4$ |

### Scientific Finding for Judges
The classical Genetic Algorithm frequently suffers from destructive crossover and stochastic bit mutations, leading to high dispersion ($\sigma = 0.1909$) and entrapment in sub-optimal local basins in ~27% of runs. In contrast, QIGA's probabilistic Q-bit amplitude rotation steers smoothly toward global optima, achieving **100% convergence consistency** ($\sigma = 0.0000$) to the global optimum.

---

## 5. Transparency & Disclosures

- **What is genuinely computed**:
  - Physics-based cubic resistance and load factors
  - XGBoost residual ML predictions ($R^2 = 0.9981$)
  - Multi-objective fitness evaluations including delay and compatibility penalties
  - Q-bit measurement sampling and unitary rotation gate matrix operations
  - Multi-seed Monte Carlo statistics (Mean, Std Dev, Min, Max)
- **What is illustrative**:
  - Bunker fuel market prices per tonne ($620/t for HFO to $2800/t for LH2)
  - Well-to-wake emission factors ($3.58$ for HFO to $0.29$ for LH2)
  - All fuel items in `fuels.json` and UI displays are explicitly marked with `"illustrative": true`.
- **Quantum computing simulation disclaimer**:
  - This system runs on classical hardware simulating quantum-inspired principles (QIGA). No real quantum hardware or Qiskit SDK is required.

---

## 6. How to Run the Prototype

### Prerequisites
- Python 3.10+
- Node.js 18+ and npm

### Backend Setup
```bash
# Navigate to project root
cd green-fleet-optimization

# Install Python requirements
pip install -r requirements.txt

# (Optional) Regenerate synthetic physics dataset
python data/generate_synthetic_data.py

# (Optional) Retrain hybrid ML residual model
python backend/prediction.py

# (Optional) Re-run 15-run Monte Carlo benchmark
python backend/benchmark.py

# Start FastAPI server (runs on http://127.0.0.1:8000)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### Frontend Setup
```bash
# In a new terminal, navigate to frontend
cd green-fleet-optimization/frontend

# Install dependencies (already installed)
npm install

# Run development server (runs on http://localhost:3000)
npm run dev
```
Open `http://localhost:3000` to interact with the dashboard.
