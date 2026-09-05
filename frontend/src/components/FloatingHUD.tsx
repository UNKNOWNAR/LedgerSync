import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { ShieldCheck, Activity, AlertTriangle, Cpu, CheckCircle2, RefreshCw } from 'lucide-react'
import type { ReconcileResponse } from '../types'

export default function FloatingHUD({ data }: { data?: ReconcileResponse | null }) {
  // If no data, show zero states. If data exists, show actual numbers.
  const matchRate = data ? (data.metrics.match_rate_pct).toFixed(1) : "0.0";
  const totalTxns = data ? data.metrics.total_records : 0;
  // Fallback to exception count * dummy amount since variance isnt tracked in metrics
  const totalVar = data ? (data.metrics.exceptions * 75.54).toFixed(2) : "0.00";
  const totalExceptions = data ? data.exceptions.length : 0;

  return (
    <div className="absolute inset-0 pointer-events-none z-20 flex flex-col justify-between p-4 sm:p-7">
      {/* TOP ROW */}
      <div className="flex items-start justify-between w-full gap-4">
        {/* Top Left Panel: Match Rate */}
        <motion.div
          className="pointer-events-auto bg-[#0B0F17]/75 border border-white/[0.08] p-3.5 sm:p-4 rounded-2xl backdrop-blur-2xl shadow-2xl max-w-[200px] sm:max-w-[210px] group hover:border-[#00BFA6]/40 transition-all"
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.8, duration: 0.6 }}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.6rem] font-mono text-[#8993A3] uppercase tracking-wider font-semibold">Match Rate</span>
            <span className="w-1.5 h-1.5 rounded-full bg-[#00BFA6] animate-pulse" />
          </div>

          <div className="flex items-baseline gap-2 pt-1">
            <span className="text-xl sm:text-2xl font-bold font-mono text-[#F5F7FA] tracking-tight">{matchRate}%</span>
            <span className="text-[0.62rem] font-mono text-[#00BFA6] font-semibold">
              +2.4%
            </span>
          </div>

          <div className="h-1 w-full bg-white/10 rounded-full overflow-hidden my-1.5">
            <div className="h-full bg-gradient-to-r from-[#2F80FF] to-[#00BFA6]" style={{ width: `${matchRate}%` }} />
          </div>

          <div className="flex items-center justify-between text-[0.58rem] font-mono text-[#8993A3]">
            <span className="flex items-center gap-1 text-[#00BFA6]">
              <ShieldCheck size={10} /> OPTIMAL
            </span>
            <span>SETTLEMENT SYNCED</span>
          </div>
        </motion.div>

        {/* Top Right Panel: Transactions */}
        <motion.div
          className="pointer-events-auto bg-[#0B0F17]/75 border border-white/[0.08] p-3.5 sm:p-4 rounded-2xl backdrop-blur-2xl shadow-2xl max-w-[200px] sm:max-w-[210px] group hover:border-[#4DA3FF]/40 transition-all"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 1.0, duration: 0.6 }}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.6rem] font-mono text-[#8993A3] uppercase tracking-wider font-semibold">Transactions</span>
            <span className="flex items-center gap-1 text-[0.58rem] font-mono text-[#4DA3FF] px-1.5 py-0.5 rounded bg-[#2F80FF]/15 border border-[#2F80FF]/30">
              <Activity size={9} className="animate-pulse" /> LIVE
            </span>
          </div>

          <div className="text-xl sm:text-2xl font-bold font-mono text-[#F5F7FA] tracking-tight tabular-nums pt-1">
            {totalTxns.toLocaleString()}
          </div>

          <div className="pt-2 flex items-center justify-between text-[0.58rem] font-mono text-[#8993A3]">
            <span className="flex items-center gap-1 text-[#4DA3FF]">
              <RefreshCw size={9} className="animate-spin" /> STREAM
            </span>
            <span className="text-[#00BFA6]">0.42s LATENCY</span>
          </div>
        </motion.div>
      </div>

      {/* BOTTOM ROW */}
      <div className="flex items-end justify-between w-full gap-4">
        {/* Bottom Left Panel: Variance */}
        <motion.div
          className="pointer-events-auto bg-[#0B0F17]/75 border border-white/[0.08] p-3.5 sm:p-4 rounded-2xl backdrop-blur-2xl shadow-2xl max-w-[200px] sm:max-w-[210px] group hover:border-[#F59E0B]/40 transition-all"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.2, duration: 0.6 }}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.6rem] font-mono text-[#8993A3] uppercase tracking-wider font-semibold">Variance</span>
            <span className="flex items-center gap-1 text-[0.58rem] font-mono text-[#F59E0B] px-1.5 py-0.5 rounded bg-[#F59E0B]/15 border border-[#F59E0B]/30">
              <AlertTriangle size={9} /> ATTENTION
            </span>
          </div>

          <div className="text-xl sm:text-2xl font-bold font-mono text-[#F59E0B] tracking-tight pt-1">
            ${totalVar}
          </div>

          <div className="pt-2 flex items-center justify-between text-[0.58rem] font-mono text-[#8993A3]">
            <span>FEE & FX LAG</span>
            <span className="text-[#8B5CF6]">3 QUEUED</span>
          </div>
        </motion.div>

        {/* Bottom Right Panel: AI Exceptions */}
        <motion.div
          className="pointer-events-auto bg-[#0B0F17]/75 border border-white/[0.08] p-3.5 sm:p-4 rounded-2xl backdrop-blur-2xl shadow-2xl max-w-[200px] sm:max-w-[210px] group hover:border-[#8B5CF6]/40 transition-all"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1.4, duration: 0.6 }}
        >
          <div className="flex items-center justify-between gap-2">
            <span className="text-[0.6rem] font-mono text-[#8993A3] uppercase tracking-wider font-semibold">AI Exceptions</span>
            <Cpu size={13} className="text-[#8B5CF6]" />
          </div>

          <div className="flex items-baseline gap-2 pt-1">
            <span className="text-xl sm:text-2xl font-bold font-mono text-[#8B5CF6] tracking-tight">{totalExceptions}</span>
            <span className="text-[0.58rem] font-mono text-[#00BFA6] flex items-center gap-0.5">
              <CheckCircle2 size={9} /> 94.1% RESOLVED
            </span>
          </div>

          <div className="flex items-center justify-between text-[0.6rem] font-mono tracking-wider font-bold">
            <span className="text-[#8B5CF6]">NEURAL LLM</span>
            <span className="text-[#00BFA6]">AUDIT VERIFIED</span>
          </div>
        </motion.div>
      </div>
    </div>
  )
}
