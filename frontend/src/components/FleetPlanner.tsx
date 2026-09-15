import React from "react";
import { Sliders, RefreshCw, Cpu, CheckCircle2 } from "lucide-react";
import { OptimizationResult } from "@/lib/api";

type AlgorithmType = "baseline" | "classical" | "quantum_inspired";

interface PlannerProps {
  cargoDemand: number;
  setCargoDemand: (val: number) => void;
  deadlineHr: number;
  setDeadlineHr: (val: number) => void;
  distanceNm: number;
  setDistanceNm: (val: number) => void;
  seaState: number;
  setSeaState: (val: number) => void;
  selectedAlgo: AlgorithmType;
  setSelectedAlgo: (val: AlgorithmType) => void;
  weightFuel: number;
  setWeightFuel: (val: number) => void;
  weightCost: number;
  setWeightCost: (val: number) => void;
  weightEmiss: number;
  setWeightEmiss: (val: number) => void;
  onSubmit: (e: React.FormEvent) => void;
  optimizing: boolean;
  activePlan: OptimizationResult | null;
}

export const FleetPlanner: React.FC<PlannerProps> = ({
  cargoDemand,
  setCargoDemand,
  deadlineHr,
  setDeadlineHr,
  distanceNm,
  setDistanceNm,
  seaState,
  setSeaState,
  selectedAlgo,
  setSelectedAlgo,
  weightFuel,
  setWeightFuel,
  weightCost,
  setWeightCost,
  weightEmiss,
  setWeightEmiss,
  onSubmit,
  optimizing,
  activePlan,
}) => {
  const algoOptions: { id: AlgorithmType; label: string }[] = [
    { id: "baseline", label: "Baseline Rule" },
    { id: "classical", label: "Classical GA" },
    { id: "quantum_inspired", label: "QIGA (Quantum)" },
  ];

  return (
    <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
      {/* Left Form: Parameters */}
      <div className="lg:col-span-5 p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <h3 className="font-semibold text-white flex items-center gap-2">
            <Sliders className="w-4 h-4 text-emerald-400" />
            Voyage & Mission Parameters
          </h3>
          <span className="text-xs text-slate-400 font-mono">Rotterdam → Gibraltar</span>
        </div>

        <form onSubmit={onSubmit} className="space-y-4">
          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">Cargo Demand:</span>
              <span className="font-mono text-emerald-400 font-semibold">{cargoDemand.toLocaleString()} tonnes</span>
            </div>
            <input
              type="range"
              min="15000"
              max="120000"
              step="5000"
              value={cargoDemand}
              onChange={(e) => setCargoDemand(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 cursor-pointer"
            />
          </div>

          <div>
            <div className="flex justify-between text-xs mb-1">
              <span className="text-slate-300">Voyage Deadline:</span>
              <span className="font-mono text-emerald-400 font-semibold">{deadlineHr} hours</span>
            </div>
            <input
              type="range"
              min="110"
              max="240"
              step="5"
              value={deadlineHr}
              onChange={(e) => setDeadlineHr(Number(e.target.value))}
              className="w-full accent-emerald-500 bg-slate-800 cursor-pointer"
            />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="block text-xs text-slate-300 mb-1">Distance (nm)</label>
              <input
                type="number"
                value={distanceNm}
                onChange={(e) => setDistanceNm(Number(e.target.value))}
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-800 text-sm font-mono text-white focus:border-emerald-500 focus:outline-none"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-300 mb-1">Sea State (Douglas 1-7)</label>
              <select
                value={seaState}
                onChange={(e) => setSeaState(Number(e.target.value))}
                className="w-full px-3 py-2 rounded bg-slate-950 border border-slate-800 text-sm font-mono text-white focus:border-emerald-500 focus:outline-none"
              >
                <option value={1}>1 - Calm (0.1m waves)</option>
                <option value={2}>2 - Smooth (0.5m waves)</option>
                <option value={3}>3 - Slight (1.2m waves)</option>
                <option value={4}>4 - Moderate (2.0m waves)</option>
                <option value={5}>5 - Rough (3.5m waves)</option>
                <option value={6}>6 - Very Rough (5.0m waves)</option>
                <option value={7}>7 - High Seas (7.0m waves)</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-300 mb-1.5 uppercase tracking-wider">
              Select Search Algorithm
            </label>
            <div className="grid grid-cols-3 gap-2">
              {algoOptions.map((algo) => (
                <button
                  key={algo.id}
                  type="button"
                  onClick={() => setSelectedAlgo(algo.id)}
                  className={`py-2 px-2 rounded-lg text-xs font-medium border text-center transition ${
                    selectedAlgo === algo.id
                      ? "bg-emerald-500/10 border-emerald-500 text-emerald-300"
                      : "bg-slate-950 border-slate-800 text-slate-400 hover:text-slate-200"
                  }`}
                >
                  {algo.label}
                </button>
              ))}
            </div>
          </div>

          <div className="p-3 rounded-lg bg-slate-950 border border-slate-800/80 space-y-2.5">
            <div className="text-xs font-semibold text-slate-400">Multi-Objective Normalization Weights</div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Fuel Weight:</span>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weightFuel}
                onChange={(e) => setWeightFuel(Number(e.target.value))}
                className="w-16 px-1.5 py-0.5 bg-slate-900 border border-slate-700 rounded text-right font-mono text-emerald-400"
              />
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Cost Weight:</span>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weightCost}
                onChange={(e) => setWeightCost(Number(e.target.value))}
                className="w-16 px-1.5 py-0.5 bg-slate-900 border border-slate-700 rounded text-right font-mono text-emerald-400"
              />
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-slate-400">Emissions Weight:</span>
              <input
                type="number"
                step="0.05"
                min="0"
                max="1"
                value={weightEmiss}
                onChange={(e) => setWeightEmiss(Number(e.target.value))}
                className="w-16 px-1.5 py-0.5 bg-slate-900 border border-slate-700 rounded text-right font-mono text-emerald-400"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={optimizing}
            className="w-full py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-semibold text-sm transition flex items-center justify-center gap-2 disabled:opacity-50"
          >
            {optimizing ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                Simulating Optimization...
              </>
            ) : (
              <>
                <Cpu className="w-4 h-4" />
                Execute {selectedAlgo === "quantum_inspired" ? "QIGA Simulation" : selectedAlgo.toUpperCase()}
              </>
            )}
          </button>
        </form>
      </div>

      {/* Right Panel: Render Optimal Plan */}
      <div className="lg:col-span-7 space-y-4">
        {activePlan ? (
          <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-slate-800">
              <div>
                <h3 className="font-semibold text-white text-base flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                  Optimized Fleet Allocation Result
                </h3>
                <p className="text-xs text-slate-400">
                  Algorithm: {activePlan.algorithm}
                </p>
              </div>
              <span className="text-xs px-2.5 py-1 rounded bg-emerald-950 border border-emerald-800 text-emerald-300 font-mono">
                Runtime: {activePlan.execution_time_ms} ms
              </span>
            </div>

            <div className="space-y-4">
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs">
                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Selected Vessel</span>
                  <span className="font-semibold text-white text-sm">{activePlan.best_plan.vessel_name}</span>
                  <span className="text-[11px] text-slate-500 block">{activePlan.best_plan.vessel_type}</span>
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Selected Fuel</span>
                  <span className="font-semibold text-emerald-400 text-sm">{activePlan.best_plan.fuel_name}</span>
                  <span className="text-[11px] text-slate-500 block">{activePlan.best_plan.fuel_type}</span>
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Cruising Speed</span>
                  <span className="font-semibold text-white text-sm font-mono">{activePlan.best_plan.speed_kn} knots</span>
                  <span className="text-[11px] text-slate-500 block">{activePlan.best_plan.voyage_duration_hr} hr voyage</span>
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Shore Power (Cold Ironing)</span>
                  <span className={`font-semibold text-sm ${activePlan.best_plan.shore_power_used ? "text-emerald-400" : "text-slate-400"}`}>
                    {activePlan.best_plan.shore_power_used ? "Active ($4.5k credit)" : "Inactive"}
                  </span>
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">Fuel Consumed</span>
                  <span className="font-semibold text-cyan-400 text-sm font-mono">{activePlan.fuel_consumed_tonnes} tonnes</span>
                  <span className="text-[11px] text-slate-500 block">via hybrid ML model</span>
                </div>

                <div className="p-3 rounded-lg bg-slate-950 border border-slate-800">
                  <span className="text-slate-400 block mb-1">WTW GHG Emissions</span>
                  <span className="font-semibold text-emerald-400 text-sm font-mono">{activePlan.emissions_co2e_tonnes} t CO₂e</span>
                  <span className="text-[11px] text-slate-500 block">Lifecycle impact</span>
                </div>
              </div>

              {/* Financial breakdown */}
              <div className="p-4 rounded-lg bg-slate-950 border border-slate-800/90 text-xs space-y-2">
                <div className="font-semibold text-slate-300 pb-1 border-b border-slate-800">Financial Voyage Breakdown</div>
                <div className="flex justify-between text-slate-400">
                  <span>Bunker Fuel Cost:</span>
                  <span className="font-mono text-slate-200">${activePlan.cost_breakdown.bunker_cost_usd.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Port Tariffs (2 calls):</span>
                  <span className="font-mono text-slate-200">${activePlan.cost_breakdown.port_costs_usd.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-slate-400">
                  <span>Shore Power Savings:</span>
                  <span className="font-mono text-emerald-400">-${activePlan.cost_breakdown.shore_power_savings_usd.toLocaleString()}</span>
                </div>
                <div className="flex justify-between text-slate-300 font-bold pt-1 border-t border-slate-800">
                  <span>Total Operating Cost:</span>
                  <span className="font-mono text-white">${activePlan.cost_breakdown.total_cost_usd.toLocaleString()}</span>
                </div>
              </div>
            </div>
          </div>
        ) : (
          <div className="p-12 text-center text-slate-500 rounded-xl bg-slate-900 border border-slate-800">
            Select parameters and click Execute Optimization to inspect fleet allocation.
          </div>
        )}
      </div>
    </div>
  );
};
