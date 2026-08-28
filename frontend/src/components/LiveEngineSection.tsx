import { motion } from 'framer-motion'
import { Cpu, ShieldCheck, Zap } from 'lucide-react'
import FinancialCore3D from './FinancialCore3D'
import FloatingHUD from './FloatingHUD'
import type { ReconcileResponse } from '../types'

export default function LiveEngineSection({ data }: { data?: ReconcileResponse | null }) {
  return (
    <div id="backend-display-section" className="relative w-full py-24 bg-[#080A0D] border-t border-white/5 flex flex-col items-center px-6 overflow-hidden">
        
      {/* Ambient Radial Gradient Glows */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[900px] h-[600px] bg-gradient-to-tr from-[#2F80FF]/10 via-[#00BFA6]/5 to-[#8B5CF6]/5 blur-[160px] pointer-events-none z-0" />
      
      {/* Grid Pattern Background */}
      <div className="absolute inset-0 bg-grid-pattern pointer-events-none z-0 opacity-30" />

      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7 }}
        className="text-center mb-12 relative z-20"
      >
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-[#2F80FF]/20 bg-[#2F80FF]/5 mb-4">
          <div className="w-1.5 h-1.5 rounded-full bg-[#2F80FF] animate-pulse" />
          <span className="text-[0.65rem] font-mono text-[#4DA3FF] uppercase tracking-widest">Live Engine · Sample Data</span>
        </div>
        <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#F5F7FA]">
          Live Reconciliation Engine
        </h2>
        <p className="text-[#8993A3] text-sm mt-2 font-medium max-w-lg mx-auto">Real-time matching pipeline parsing transaction rows via multi-tier deterministic algorithms.</p>
      </motion.div>

      {/* 3D WebGL Core Container */}
      <motion.div
        initial={{ opacity: 0, y: 40 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: "-100px" }}
        transition={{ duration: 0.9 }}
        className="relative w-full max-w-6xl z-10"
      >
        {/* Ambient glow that grounds the canvas */}
        <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-b from-[#2F80FF]/10 via-[#00BFA6]/6 to-transparent blur-2xl pointer-events-none" />
        <div className="absolute -bottom-6 left-1/4 right-1/4 h-12 bg-[#2F80FF]/15 blur-2xl rounded-full pointer-events-none" />

        <div className="relative h-[550px] sm:h-[700px] rounded-3xl border border-[#2F80FF]/20 fintech-glass-panel overflow-hidden shadow-[0_0_60px_rgba(47,128,255,0.08),0_32px_64px_rgba(0,0,0,0.6)]">
          <FloatingHUD />
          <FinancialCore3D data={data} />
        </div>
      </motion.div>

      {/* Institutional Spec Cards Row */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.7, delay: 0.2 }}
        className="w-full max-w-5xl mt-16 z-20 relative"
      >
        {/* Section label */}
        <div className="flex items-center gap-3 mb-6">
          <div className="h-px flex-1 bg-white/[0.06]" />
          <span className="text-[0.6rem] font-mono text-[#3A4454] uppercase tracking-widest">Engine Capabilities</span>
          <div className="h-px flex-1 bg-white/[0.06]" />
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-left">
          <div className="group fintech-glass-panel p-5 rounded-2xl border border-white/[0.06] hover:border-[#2F80FF]/20 bg-gradient-to-b from-white/[0.02] to-transparent flex items-start gap-3 transition-all duration-300">
            <div className="w-10 h-10 rounded-xl bg-[#2F80FF]/10 border border-[#2F80FF]/20 flex items-center justify-center text-[#4DA3FF] shrink-0 group-hover:bg-[#2F80FF]/15 transition-colors">
              <Zap size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-[#F5F7FA] font-sans">Sub-Second Processing</div>
              <div className="text-xs text-[#6B7280] mt-1 leading-relaxed">Parses 50k+ ledger records in sub-second memory execution without lag.</div>
            </div>
          </div>

          <div className="group fintech-glass-panel p-5 rounded-2xl border border-white/[0.06] hover:border-[#8B5CF6]/20 bg-gradient-to-b from-white/[0.02] to-transparent flex items-start gap-3 transition-all duration-300">
            <div className="w-10 h-10 rounded-xl bg-[#8B5CF6]/10 border border-[#8B5CF6]/20 flex items-center justify-center text-[#8B5CF6] shrink-0 group-hover:bg-[#8B5CF6]/15 transition-colors">
              <Cpu size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-[#F5F7FA] font-sans">Deep LLM Reasoning</div>
              <div className="text-xs text-[#6B7280] mt-1 leading-relaxed">Autonomous natural language reasoning over fee & FX variance edge-cases.</div>
            </div>
          </div>

          <div className="group fintech-glass-panel p-5 rounded-2xl border border-white/[0.06] hover:border-[#00BFA6]/20 bg-gradient-to-b from-white/[0.02] to-transparent flex items-start gap-3 transition-all duration-300">
            <div className="w-10 h-10 rounded-xl bg-[#00BFA6]/10 border border-[#00BFA6]/20 flex items-center justify-center text-[#00BFA6] shrink-0 group-hover:bg-[#00BFA6]/15 transition-colors">
              <ShieldCheck size={18} />
            </div>
            <div>
              <div className="text-sm font-bold text-[#F5F7FA] font-sans">SOX / Audit Compliant</div>
              <div className="text-xs text-[#6B7280] mt-1 leading-relaxed">Generates machine-readable JSONL ledgers & immutable executive reports.</div>
            </div>
          </div>
        </div>
      </motion.div>

    </div>
  )
}
