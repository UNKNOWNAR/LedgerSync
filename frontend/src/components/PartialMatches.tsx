import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ChevronDown, Check, X, Cpu, AlertCircle } from 'lucide-react'
import type { MatchResult, Transaction } from '../types'

function RecordCard({ tx, label }: { tx: Transaction | null; label: string }) {
  if (!tx) {
    return (
      <div className="rounded-xl p-3.5 bg-white/[0.02] border border-white/[0.06]">
        <div className="text-[0.68rem] font-semibold text-zinc-400 uppercase tracking-wider mb-2">
          {label}
        </div>
        <div className="text-xs text-zinc-400">No matching record</div>
      </div>
    )
  }

  const rows = [
    ['Transaction ID', tx.transaction_id],
    ['Amount', `₹${tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}`],
    ['Settlement Date', tx.date],
    ['Merchant Name', tx.merchant_name],
    ['Reference Number', tx.reference_number],
  ]

  return (
    <div className="rounded-xl p-3.5 bg-white/[0.03] border border-white/[0.06]">
      <div className="text-[0.68rem] font-semibold text-zinc-400 uppercase tracking-wider mb-2.5">
        {label}
      </div>
      <div className="space-y-1.5">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between items-center text-xs py-0.5">
            <span className="text-zinc-400 font-medium">{k}</span>
            <span className="text-zinc-100 font-medium tabular-nums">{v}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100)
  const colorClass = value >= 0.85 ? 'bg-emerald-500 text-emerald-400' : value >= 0.6 ? 'bg-amber-500 text-amber-400' : 'bg-rose-500 text-rose-400'

  return (
    <div className="flex items-center gap-2">
      <div className="w-14 h-1.5 rounded-full bg-white/[0.08] overflow-hidden">
        <motion.div
          className={`h-full rounded-full ${colorClass.split(' ')[0]}`}
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.5, ease: 'easeOut' }}
        />
      </div>
      <span className={`text-xs font-semibold tabular-nums ${colorClass.split(' ')[1]}`}>
        {pct}%
      </span>
    </div>
  )
}

export default function PartialMatches({ matches }: { matches: MatchResult[] }) {
  const [approvals, setApprovals] = useState<Record<string, 'approved' | 'rejected'>>({})
  const [expanded, setExpanded] = useState<string | null>(null)

  if (matches.length === 0) {
    return (
      <div className="text-center py-12 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-xs text-zinc-400">
        No partial matches pending review — all candidates fully resolved.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-zinc-400">
        Inspect fuzzy candidates and confirm or reject discrepancies below.
      </p>

      {matches.map((m, i) => {
        const id = m.gateway_tx?.transaction_id ?? `pm_${i}`
        const isOpen = expanded === id
        const approval = approvals[id]

        return (
          <motion.div
            key={id}
            className="rounded-2xl overflow-hidden border transition-colors select-none"
            style={{
              background: 'rgba(255, 255, 255, 0.03)',
              borderColor: isOpen ? 'rgba(255, 255, 255, 0.16)' : 'rgba(255, 255, 255, 0.08)',
              backdropFilter: 'blur(16px)',
            }}
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.04, duration: 0.4 }}
          >
            <button
              type="button"
              onClick={() => setExpanded(isOpen ? null : id)}
              className="w-full flex items-center justify-between px-5 py-4 text-left hover:bg-white/[0.02] transition-colors cursor-pointer"
            >
              <div className="flex items-center gap-4">
                <span className="text-xs font-mono text-zinc-400">#{i + 1}</span>
                <ConfidenceMeter value={m.confidence} />
                {m.discrepancy_notes[0] && (
                  <span className="text-xs text-zinc-300 truncate max-w-sm">
                    {m.discrepancy_notes[0]}
                  </span>
                )}
                {approval && (
                  <motion.span
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[0.68rem] font-semibold ${
                      approval === 'approved'
                        ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                        : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                    }`}
                  >
                    {approval === 'approved' ? 'Approved' : 'Rejected'}
                  </motion.span>
                )}
              </div>
              <motion.div
                animate={{ rotate: isOpen ? 180 : 0 }}
                transition={{ duration: 0.2 }}
                className="text-zinc-400"
              >
                <ChevronDown size={18} />
              </motion.div>
            </button>

            <AnimatePresence>
              {isOpen && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.25, ease: 'easeInOut' }}
                  className="overflow-hidden border-t border-white/[0.06]"
                >
                  <div className="p-5 space-y-4 bg-white/[0.01]">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <RecordCard tx={m.gateway_tx} label="Gateway Transaction" />
                      <RecordCard tx={m.bank_tx} label="Bank Statement" />
                    </div>

                    {m.discrepancy_notes.length > 0 && (
                      <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/20 space-y-1">
                        <div className="flex items-center gap-1.5 text-amber-400 text-xs font-semibold">
                          <AlertCircle size={14} />
                          <span>Detected Discrepancies</span>
                        </div>
                        <ul className="space-y-0.5 pl-5 list-disc text-xs text-amber-200/80">
                          {m.discrepancy_notes.map((note, j) => (
                            <li key={j}>{note}</li>
                          ))}
                        </ul>
                      </div>
                    )}

                    {m.llm_reasoning && (
                      <div className="p-3.5 rounded-xl bg-purple-500/10 border border-purple-500/20 space-y-1">
                        <div className="flex items-center gap-1.5 text-xs font-semibold text-[#F5F7FA] mb-2">
                          <Cpu size={14} className="text-[#4DA3FF]" />
                          <span>Resolution Synthesis</span>
                        </div>
                        <p className="text-xs text-purple-100/90 leading-relaxed font-normal">
                          {m.llm_reasoning}
                        </p>
                      </div>
                    )}

                    <div className="flex items-center gap-3 pt-2">
                      <button
                        type="button"
                        onClick={() => setApprovals((a) => ({ ...a, [id]: 'approved' }))}
                        className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                          approval === 'approved'
                            ? 'bg-emerald-500 text-white font-semibold shadow-md shadow-emerald-500/20'
                            : 'bg-white/[0.06] hover:bg-white/[0.12] text-emerald-400 border border-emerald-500/30'
                        }`}
                      >
                        <Check size={14} />
                        Approve Match
                      </button>
                      <button
                        type="button"
                        onClick={() => setApprovals((a) => ({ ...a, [id]: 'rejected' }))}
                        className={`inline-flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-medium transition-all cursor-pointer ${
                          approval === 'rejected'
                            ? 'bg-rose-500 text-white font-semibold shadow-md shadow-rose-500/20'
                            : 'bg-white/[0.06] hover:bg-white/[0.12] text-rose-400 border border-rose-500/30'
                        }`}
                      >
                        <X size={14} />
                        Reject Candidate
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )
      })}
    </div>
  )
}
