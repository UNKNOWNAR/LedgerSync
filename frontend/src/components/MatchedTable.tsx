import { motion } from 'framer-motion'
import type { MatchResult } from '../types'

export default function MatchedTable({ matches }: { matches: MatchResult[] }) {
  if (matches.length === 0) {
    return (
      <div className="text-center py-12 rounded-2xl bg-white/[0.02] border border-white/[0.06] text-xs text-zinc-400">
        No matched records found.
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
              {['Status', 'Confidence', 'Gateway ID', 'Bank ID', 'GW Amount', 'Bank Amount', 'GW Date', 'Bank Date', 'Merchant', 'Reference'].map((h) => (
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
            {matches.map((m, i) => {
              const isExact = m.status === 'exact'
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
                      className={`inline-flex px-2 py-0.5 rounded-full text-[0.68rem] font-semibold capitalize ${
                        isExact
                          ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
                          : 'bg-blue-500/15 text-blue-400 border border-blue-500/30'
                      }`}
                    >
                      {m.status.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono font-semibold tabular-nums text-zinc-200">
                    {Math.round(m.confidence * 100)}%
                  </td>
                  <td className="px-4 py-3 font-mono font-medium text-zinc-200">{m.gateway_tx?.transaction_id ?? '—'}</td>
                  <td className="px-4 py-3 font-mono font-medium text-zinc-200">{m.bank_tx?.transaction_id ?? '—'}</td>
                  <td className="px-4 py-3 font-mono text-white font-medium">
                    {m.gateway_tx ? `₹${m.gateway_tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-white font-medium">
                    {m.bank_tx ? `₹${m.bank_tx.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}` : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-zinc-400">{m.gateway_tx?.date ?? '—'}</td>
                  <td className="px-4 py-3 font-mono text-zinc-400">{m.bank_tx?.date ?? '—'}</td>
                  <td className="px-4 py-3 text-zinc-300">{m.gateway_tx?.merchant_name ?? '—'}</td>
                  <td className="px-4 py-3 font-mono text-zinc-400">{m.gateway_tx?.reference_number ?? '—'}</td>
                </motion.tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
