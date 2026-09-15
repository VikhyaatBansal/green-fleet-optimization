import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "GreenFleet Quanta — SIH 26138 Maritime Optimization",
  description: "Quantum-Inspired Green Fleet Optimization & Fuel Prediction Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="bg-slate-950 text-slate-100 min-h-screen flex flex-col antialiased selection:bg-emerald-500 selection:text-black">
        <main className="flex-1">
          {children}
        </main>
        <footer className="border-t border-slate-800/80 bg-slate-900/60 backdrop-blur py-4 px-6 text-center text-xs text-slate-400">
          <div className="max-w-4xl mx-auto">
            <p className="text-slate-400 italic text-center">
              Prototype built on synthetic, physics-anchored data. Fuel/emission constants are illustrative. Quantum-inspired optimizer is a classical simulation of quantum-inspired search — no quantum hardware is used.
            </p>
          </div>
        </footer>
      </body>
    </html>
  );
}
