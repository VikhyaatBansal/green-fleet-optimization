"use client";

import React, { useState, useEffect } from "react";
import {
  fetchFuels,
  fetchMetrics,
  runOptimize,
  runFuelScenario,
  fetchBenchmark,
  Fuel,
  MLMetrics,
  OptimizationResult,
  FuelScenarioItem,
  BenchmarkResponse,
} from "@/lib/api";
import { Header } from "@/components/Header";
import { ExecutiveOverview } from "@/components/ExecutiveOverview";
import { FleetPlanner } from "@/components/FleetPlanner";
import { FuelScenarios } from "@/components/FuelScenarios";
import { AlgorithmComparison } from "@/components/AlgorithmComparison";
import { BenchmarkView } from "@/components/BenchmarkView";
import { Layers, Sliders, BarChart3, Gauge, CheckCircle2, AlertTriangle, RefreshCw } from "lucide-react";

type TabType = "overview" | "planner" | "scenarios" | "comparison" | "benchmark";
type AlgorithmType = "baseline" | "classical" | "quantum_inspired";

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState<TabType>("overview");

  const [fuels, setFuels] = useState<Fuel[]>([]);
  const [metrics, setMetrics] = useState<MLMetrics | null>(null);

  const [baselineOpt, setBaselineOpt] = useState<OptimizationResult | null>(null);
  const [classicalOpt, setClassicalOpt] = useState<OptimizationResult | null>(null);
  const [qigaOpt, setQigaOpt] = useState<OptimizationResult | null>(null);
  const [fuelScenarios, setFuelScenarios] = useState<FuelScenarioItem[]>([]);
  const [benchmarkData, setBenchmarkData] = useState<BenchmarkResponse | null>(null);

  // Planner form state
  const [cargoDemand, setCargoDemand] = useState<number>(45000);
  const [deadlineHr, setDeadlineHr] = useState<number>(160);
  const [distanceNm, setDistanceNm] = useState<number>(2200);
  const [seaState, setSeaState] = useState<number>(3);
  const [selectedAlgo, setSelectedAlgo] = useState<AlgorithmType>("quantum_inspired");
  const [weightFuel, setWeightFuel] = useState<number>(0.35);
  const [weightCost, setWeightCost] = useState<number>(0.35);
  const [weightEmiss, setWeightEmiss] = useState<number>(0.30);

  const [loading, setLoading] = useState<boolean>(true);
  const [optimizing, setOptimizing] = useState<boolean>(false);
  const [apiError, setApiError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInitialData() {
      try {
        setLoading(true);
        setApiError(null);
        const [fData, mData, bench] = await Promise.all([
          fetchFuels(),
          fetchMetrics(),
          fetchBenchmark(false),
        ]);
        setFuels(fData);
        setMetrics(mData);
        setBenchmarkData(bench);

        const [bRes, cRes, qRes, scRes] = await Promise.all([
          runOptimize({ algorithm: "baseline", cargo_demand_tonnes: 45000, deadline_hr: 160 }),
          runOptimize({ algorithm: "classical", cargo_demand_tonnes: 45000, deadline_hr: 160, pop_size: 25, generations: 30 }),
          runOptimize({ algorithm: "quantum_inspired", cargo_demand_tonnes: 45000, deadline_hr: 160, pop_size: 25, generations: 30 }),
          runFuelScenario(45000, 160),
        ]);

        setBaselineOpt(bRes);
        setClassicalOpt(cRes);
        setQigaOpt(qRes);
        setFuelScenarios(scRes.results);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Failed connecting to backend API";
        console.error("Initialization error:", err);
        setApiError(`${msg}. Please ensure the FastAPI backend is running on port 8000.`);
      } finally {
        setLoading(false);
      }
    }
    loadInitialData();
  }, []);

  async function handlePlannerSubmit(e: React.FormEvent) {
    e.preventDefault();
    try {
      setOptimizing(true);
      setApiError(null);
      const res = await runOptimize({
        algorithm: selectedAlgo,
        cargo_demand_tonnes: cargoDemand,
        deadline_hr: deadlineHr,
        distance_nm: distanceNm,
        sea_state: seaState,
        weights: {
          fuel: weightFuel,
          cost: weightCost,
          emissions: weightEmiss,
          delay: 1.0,
        },
        pop_size: 30,
        generations: 40,
      });

      if (selectedAlgo === "baseline") setBaselineOpt(res);
      else if (selectedAlgo === "classical") setClassicalOpt(res);
      else setQigaOpt(res);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Optimization request failed";
      setApiError(msg);
    } finally {
      setOptimizing(false);
    }
  }

  const activePlan =
    selectedAlgo === "baseline"
      ? baselineOpt
      : selectedAlgo === "classical"
      ? classicalOpt
      : qigaOpt;

  return (
    <div className="max-w-7xl mx-auto px-4 py-6 space-y-6">
      <Header r2Score={metrics?.hybrid_metrics.r2_score} />

      {apiError && (
        <div className="p-4 rounded-lg bg-rose-950/40 border border-rose-800 text-rose-300 text-sm flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />
            <span>{apiError}</span>
          </div>
          <span className="text-xs text-rose-400 font-mono">FastAPI: http://127.0.0.1:8000</span>
        </div>
      )}

      {loading && (
        <div className="p-8 rounded-xl bg-slate-900 border border-slate-800 text-center space-y-3">
          <RefreshCw className="w-8 h-8 text-emerald-400 animate-spin mx-auto" />
          <div className="text-sm font-semibold text-white">Initializing Quantum Green Fleet Engine...</div>
          <div className="text-xs text-slate-400">Loading physics models, vessel fleet data, and baseline comparison.</div>
        </div>
      )}

      {/* Navigation Tabs */}
      <nav className="flex space-x-2 border-b border-slate-800 overflow-x-auto pb-1 text-sm font-medium">
        {[
          { id: "overview", label: "Executive Overview", icon: Layers },
          { id: "planner", label: "Fleet Voyage Planner", icon: Sliders },
          { id: "scenarios", label: "Fuel Scenario Analysis", icon: BarChart3 },
          { id: "comparison", label: "Algorithm Convergence", icon: Gauge },
          { id: "benchmark", label: "15-Run Monte Carlo Benchmark", icon: CheckCircle2 },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as TabType)}
              className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition whitespace-nowrap ${
                isActive
                  ? "bg-slate-900 text-emerald-400 border-b-2 border-emerald-400 font-semibold"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-900/40"
              }`}
            >
              <Icon className="w-4 h-4" />
              {tab.label}
            </button>
          );
        })}
      </nav>

      {/* Tab Panels */}
      {!loading && activeTab === "overview" && (
        <ExecutiveOverview
          baselineOpt={baselineOpt}
          qigaOpt={qigaOpt}
          metrics={metrics}
          cargoDemand={cargoDemand}
        />
      )}

      {!loading && activeTab === "planner" && (
        <FleetPlanner
          cargoDemand={cargoDemand}
          setCargoDemand={setCargoDemand}
          deadlineHr={deadlineHr}
          setDeadlineHr={setDeadlineHr}
          distanceNm={distanceNm}
          setDistanceNm={setDistanceNm}
          seaState={seaState}
          setSeaState={setSeaState}
          selectedAlgo={selectedAlgo}
          setSelectedAlgo={setSelectedAlgo}
          weightFuel={weightFuel}
          setWeightFuel={setWeightFuel}
          weightCost={weightCost}
          setWeightCost={setWeightCost}
          weightEmiss={weightEmiss}
          setWeightEmiss={setWeightEmiss}
          onSubmit={handlePlannerSubmit}
          optimizing={optimizing}
          activePlan={activePlan}
        />
      )}

      {!loading && activeTab === "scenarios" && (
        <FuelScenarios fuelScenarios={fuelScenarios} fuels={fuels} />
      )}

      {!loading && activeTab === "comparison" && (
        <AlgorithmComparison
          baselineOpt={baselineOpt}
          classicalOpt={classicalOpt}
          qigaOpt={qigaOpt}
        />
      )}

      {!loading && activeTab === "benchmark" && benchmarkData && (
        <BenchmarkView benchmarkData={benchmarkData} />
      )}
    </div>
  );
}
