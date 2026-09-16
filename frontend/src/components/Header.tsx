import React from "react";
import Image from "next/image";
import { RefreshCw } from "lucide-react";

interface HeaderProps {
  r2Score?: number;
}

export const Header: React.FC<HeaderProps> = ({ r2Score = 0.9981 }) => {
  return (
    <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-5 border-b border-slate-800">
      <div className="flex items-center gap-3">
        <div className="relative w-11 h-11 rounded-lg bg-emerald-950/40 border border-emerald-500/30 p-1 flex items-center justify-center overflow-hidden shadow-inner shrink-0">
          <Image
            src="/logo.png"
            alt="GreenFleet Quanta Logo"
            width={40}
            height={40}
            className="w-full h-full object-contain"
            priority
          />
        </div>

        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white whitespace-nowrap">
            GreenFleet Quanta
          </h1>

          <p className="text-xs text-slate-400">
            Quantum-Inspired Maritime Fuel Consumption Prediction & Green Fleet Optimization Engine
          </p>
        </div>
      </div>

      <div className="flex flex-wrap items-center gap-2 text-xs font-mono">
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
          Hybrid ML R²: {r2Score}
        </div>

        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-md bg-slate-900 border border-slate-800 text-slate-300">
          <span className="w-2 h-2 rounded-full bg-cyan-400"></span>
          Simulation: QIGA (11 Q-bits)
        </div>

        <button
          onClick={() => window.location.reload()}
          className="flex items-center gap-1 px-3 py-1.5 rounded-md bg-slate-800 hover:bg-slate-700 text-slate-200 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          Refresh
        </button>
      </div>
    </header>
  );
};
