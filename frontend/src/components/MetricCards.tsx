import { motion } from 'framer-motion'
import { Target, Search, AlertTriangle, XCircle, BarChart3, AlertOctagon } from 'lucide-react'
import type { Metrics } from '../types'
import Card3D from './Card3D'

const cards = [
  { key: 'match_rate', label: 'Match Rate', icon: BarChart3, format: (m: Metrics) => `${m.match_rate_pct}%`, sub: 'Overall efficiency', color: 'text-emerald-400', glow: 'shadow-emerald-500/10' },
  { key: 'exact', label: 'Exact Matches', icon: Target, format: (m: Metrics) => String(m.exact_matches), sub: 'Strict reference match', color: 'text-blue-400', glow: 'shadow-blue-500/10' },
  { key: 'fuzzy', label: 'Fuzzy Matches', icon: Search, format: (m: Metrics) => String(m.fuzzy_llm_matches + m.fuzzy_rule_matches), sub: 'AI + Rule candidate', color: 'text-purple-400', glow: 'shadow-purple-500/10' },
  { key: 'partial', label: 'Partial Review', icon: AlertTriangle, format: (m: Metrics) => String(m.partial_matches), sub: 'Requires decision', color: 'text-amber-400', glow: 'shadow-amber-500/10' },
  { key: 'exceptions', label: 'Exceptions', icon: XCircle, format: (m: Metrics) => String(m.exceptions), sub: 'Unmatched records', color: 'text-rose-400', glow: 'shadow-rose-500/10' },
  { key: 'ingest', label: 'Parse Errors', icon: AlertOctagon, format: (m: Metrics) => String(m.ingestion_errors), sub: 'Invalid row formats', color: 'text-zinc-400', glow: 'shadow-zinc-500/10' },
] as const

export default function MetricCards({ metrics }: { metrics: Metrics }) {
  return (
    <div className="space-y-3 pt-6">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-[0.08em] text-zinc-400 uppercase flex items-center gap-2">
          <span>3D Reconciliation Metrics</span>
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500 animate-pulse" />
        </h3>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {cards.map((card, i) => {
          const Icon = card.icon
          return (
            <motion.div
              key={card.key}
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: i * 0.05,
                duration: 0.4,
                ease: [0.16, 1, 0.3, 1],
              }}
            >
              <Card3D intensity={12}>
                <div
                  className={`relative rounded-2xl p-4 border select-none transition-all duration-300 group shadow-lg ${card.glow}`}
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                    backdropFilter: 'blur(16px)',
                    transformStyle: 'preserve-3d',
                  }}
                >
                  <div className="flex items-center justify-between mb-2" style={{ transform: 'translateZ(12px)' }}>
                    <span className="text-[0.68rem] font-medium text-zinc-400 uppercase tracking-wider">
                      {card.label}
                    </span>
                    <div className="w-7 h-7 rounded-lg bg-white/[0.05] border border-white/10 flex items-center justify-center">
                      <Icon size={15} className={card.color} strokeWidth={2} />
                    </div>
                  </div>

                  <motion.div
                    className="text-2xl font-bold text-white tracking-tight tabular-nums"
                    style={{ transform: 'translateZ(20px)' }}
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ delay: i * 0.05 + 0.1, duration: 0.3 }}
                  >
                    {card.format(metrics)}
                  </motion.div>

                  <div className="text-[0.68rem] text-zinc-400 mt-1 truncate" style={{ transform: 'translateZ(8px)' }}>
                    {card.sub}
                  </div>
                </div>
              </Card3D>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
