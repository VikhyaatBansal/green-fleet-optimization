import React from "react";
import { BarChart3 } from "lucide-react";
import { FuelScenarioItem, Fuel } from "@/lib/api";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from "recharts";

interface ScenariosProps {
  fuelScenarios: FuelScenarioItem[];
  fuels: Fuel[];
}

export const FuelScenarios: React.FC<ScenariosProps> = ({ fuelScenarios, fuels }) => {
  return (
    <div className="space-y-6">
      <div className="p-6 rounded-xl bg-slate-900 border border-slate-800 space-y-4">
        <div className="flex items-center justify-between pb-3 border-b border-slate-800">
          <div>
            <h3 className="font-semibold text-white text-base flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-400" />
              Comparative Alternative Fuel Evaluation (45,000t Demand)
            </h3>
            <p className="text-xs text-slate-400">
              Each fuel alternative is independently evaluated by the QIGA optimizer under identical voyage demands.
            </p>
          </div>
          <span className="text-xs px-2.5 py-1 rounded bg-slate-800 text-slate-300 font-mono">
            5 Fuel Types Evaluated
          </span>
        </div>

        {/* Recharts Bar Chart: Emissions vs Cost */}
        <div className="h-80 w-full pt-4">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={fuelScenarios} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
              <XAxis dataKey="fuel_id" stroke="#94a3b8" />
              <YAxis yAxisId="left" orientation="left" stroke="#10b981" />
              <YAxis yAxisId="right" orientation="right" stroke="#38bdf8" />
              <Tooltip
                contentStyle={{ backgroundColor: "#0f172a", borderColor: "#334155", color: "#f8fafc" }}
              />
              <Legend />
              <Bar yAxisId="left" dataKey="emissions_co2e_tonnes" name="Emissions (tonnes CO₂e)" fill="#10b981" radius={[4, 4, 0, 0]} />
              <Bar yAxisId="right" dataKey="cost_usd" name="Total Voyage Cost ($)" fill="#38bdf8" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Fuel Properties Reference Table */}
        <div className="overflow-x-auto pt-4">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="border-b border-slate-800 text-slate-400 font-semibold">
                <th className="py-2.5 px-3">Fuel Type</th>
                <th className="py-2.5 px-3">Relative Energy Density</th>
                <th className="py-2.5 px-3">Cost / Tonne (USD)</th>
                <th className="py-2.5 px-3">WTW Emission Factor</th>
                <th className="py-2.5 px-3">Simulated Consumption</th>
                <th className="py-2.5 px-3">Resulting Emissions</th>
                <th className="py-2.5 px-3">Total Cost</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/60 font-mono">
              {fuelScenarios.map((sc) => {
                const fuelMeta = fuels.find((f) => f.fuel_id === sc.fuel_id);
                return (
                  <tr key={sc.fuel_id} className="hover:bg-slate-800/30">
                    <td className="py-2.5 px-3 font-semibold text-white flex items-center gap-1.5">
                      {sc.fuel_id}
                      <span className="text-[10px] px-1 rounded bg-slate-800 text-slate-400 font-sans">illustrative</span>
                    </td>
                    <td className="py-2.5 px-3 text-slate-300">{fuelMeta?.energy_density_relative}x HFO</td>
                    <td className="py-2.5 px-3 text-slate-300">${fuelMeta?.cost_per_tonne_usd.toLocaleString()}</td>
                    <td className="py-2.5 px-3 text-slate-300">{fuelMeta?.emission_factor_co2e_per_tonne} t/t</td>
                    <td className="py-2.5 px-3 text-cyan-400">{sc.fuel_consumed_tonnes} t</td>
                    <td className="py-2.5 px-3 text-emerald-400 font-bold">{sc.emissions_co2e_tonnes} t CO₂e</td>
                    <td className="py-2.5 px-3 text-slate-200">${sc.cost_usd.toLocaleString()}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
