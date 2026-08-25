import { motion } from 'framer-motion'
import type { ReconcileResponse } from '../types'

export default function AuditTrail({ data }: { data: ReconcileResponse }) {
  const all = [...data.matched, ...data.partial_matches, ...data.exceptions]

  if (all.length === 0) {
    return (
      <div className="text-center py-12 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-xs text-zinc-400">
        No audit trail records available.
      </div>
    )
  }

  return (
    <div className="space-y-3">
      <p className="text-xs text-zinc-400">
        Immutable decision ledger logging validation status, rule scores, and timestamp metadata.
      </p>

      <motion.div
        className="rounded-2xl overflow-hidden border border-white/[0.08]"
        style={{
          background: 'rgba(255, 255, 255, 0.03)',
          backdropFilter: 'blur(16px)',
        }}
        initial={{ opacity: 0, scale: 0.99 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
      >
        <div className="overflow-x-auto">
          <table className="w-full text-xs text-left border-collapse">
            <thead>
              <tr className="bg-white/[0.04] border-b border-white/[0.08]">
                {['GW TX ID', 'Bank TX ID', 'Decision', 'Confidence', 'Rule Score', 'AI Engine', 'Synthesis', 'Timestamp'].map((h) => (
                  <th
                    key={h}
                    className="px-4 py-3 text-[0.68rem] font-semibold text-zinc-400 uppercase tracking-wider whitespace-nowrap"
                  >
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {all.map((m, i) => {
                const isExact = m.status === 'exact'
                const isException = m.status === 'exception'

                return (
                  <motion.tr
                    key={i}
                    className="hover:bg-white/[0.03] transition-colors"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    transition={{ delay: i * 0.015 }}
                  >
                    <td className="px-4 py-3 font-mono font-medium text-zinc-200">{m.gateway_tx?.transaction_id ?? '—'}</td>
                    <td className="px-4 py-3 font-mono font-medium text-zinc-200">{m.bank_tx?.transaction_id ?? '—'}</td>
                    <td className="px-4 py-3">
                      <span
                        className={`inline-flex px-2 py-0.5 rounded-full text-[0.68rem] font-semibold ${
                          isExact
                            ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                            : isException
                            ? 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                            : 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                        }`}
                      >
                        {m.status}
                      </span>
                    </td>
                    <td className="px-4 py-3 font-mono font-medium text-zinc-100">{Math.round(m.confidence * 100)}%</td>
                    <td className="px-4 py-3 font-mono text-zinc-400">{Math.round(m.rule_score * 100)}%</td>
                    <td className="px-4 py-3">
                      <span className={m.llm_available ? 'text-purple-400 font-medium' : 'text-zinc-400'}>
                        {m.llm_available ? 'Claude 3.5' : 'Rule Engine'}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-zinc-400 max-w-xs truncate">
                      {m.llm_reasoning || m.discrepancy_notes.join(' · ') || 'Exact reference match'}
                    </td>
                    <td className="px-4 py-3 font-mono text-zinc-400 whitespace-nowrap">
                      {m.matched_at ?? '—'}
                    </td>
                  </motion.tr>
                )
              })}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  )
}
