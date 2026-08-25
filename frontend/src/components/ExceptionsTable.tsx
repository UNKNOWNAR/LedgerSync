import { motion } from 'framer-motion'
import type { MatchResult } from '../types'

export default function ExceptionsTable({ exceptions }: { exceptions: MatchResult[] }) {
  if (exceptions.length === 0) {
    return (
      <div className="text-center py-12 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-xs text-zinc-400">
        No exceptions — all transactions fully matched.
      </div>
    )
  }

  return (
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
              {['Source', 'Transaction ID', 'Amount', 'Date', 'Merchant Name', 'Reference Number', 'Discrepancy Reason'].map((h) => (
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
            {exceptions.map((m, i) => {
              const tx = m.gateway_tx || m.bank_tx
              const source = m.gateway_tx ? 'Gateway' : m.bank_tx ? 'Bank' : 'Ingestion'

              return (
                <motion.tr
                  key={i}
                  className="hover:bg-white/[0.03] transition-colors"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  transition={{ delay: i * 0.02 }}
                >
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex px-2 py-0.5 rounded-full text-[0.68rem] font-semibold ${
                        source === 'Gateway'
                          ? 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                          : source === 'Bank'
                          ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
                          : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
                      }`}
                    >
                      {source}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-medium text-zinc-200">{tx?.transaction_id ?? 'N/A'}</td>
                  <td className="px-4 py-3 font-mono font-semibold text-white">
                    {tx ? `₹${tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : 'N/A'}
                  </td>
                  <td className="px-4 py-3 font-mono text-zinc-400">{tx?.date ?? 'N/A'}</td>
                  <td className="px-4 py-3 text-zinc-300 font-medium">{tx?.merchant_name ?? 'N/A'}</td>
                  <td className="px-4 py-3 font-mono text-zinc-400">{tx?.reference_number ?? 'N/A'}</td>
                  <td className="px-4 py-3 text-zinc-400 max-w-xs truncate">
                    {m.discrepancy_notes.join(' · ') || 'Unmatched'}
                  </td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
