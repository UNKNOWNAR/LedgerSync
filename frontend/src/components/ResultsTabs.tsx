import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { ReconcileResponse } from '../types'
import PartialMatches from './PartialMatches'
import ExceptionsTable from './ExceptionsTable'
import MatchedTable from './MatchedTable'
import AuditTrail from './AuditTrail'

const tabs = [
  { id: 'partial', label: 'Partial Matches' },
  { id: 'exceptions', label: 'Exceptions' },
  { id: 'matched', label: 'Matched Records' },
  { id: 'audit', label: 'Audit Trail' },
] as const

type TabId = (typeof tabs)[number]['id']

export default function ResultsTabs({ data }: { data: ReconcileResponse }) {
  const [active, setActive] = useState<TabId>('partial')

  const counts: Record<TabId, number> = {
    partial: data.partial_matches.length,
    exceptions: data.exceptions.length,
    matched: data.matched.length,
    audit: data.matched.length + data.partial_matches.length + data.exceptions.length,
  }

  return (
    <div className="space-y-4 pt-6">
      {/* Sliding Pill Tab Bar */}
      <div className="inline-flex items-center p-1 rounded-2xl bg-white/[0.04] border border-white/[0.08] backdrop-blur-md select-none">
        {tabs.map((tab) => {
          const isActive = active === tab.id
          return (
            <button
              key={tab.id}
              onClick={() => setActive(tab.id)}
              className="relative px-4 py-2 text-xs font-medium rounded-xl transition-colors duration-200 flex items-center gap-2 cursor-pointer"
              style={{
                color: isActive ? '#ffffff' : 'rgba(255, 255, 255, 0.55)',
              }}
            >
              {isActive && (
                <motion.div
                  layoutId="activeTab"
                  className="absolute inset-0 rounded-xl bg-white/[0.12] border border-white/[0.16] shadow-sm"
                  transition={{ type: 'spring', stiffness: 500, damping: 35 }}
                />
              )}
              <span className="relative z-10">{tab.label}</span>
              <span
                className={`relative z-10 px-1.5 py-0.5 rounded-full text-[0.68rem] font-semibold tabular-nums transition-colors ${
                  isActive ? 'bg-white/20 text-white' : 'bg-white/[0.06] text-zinc-400'
                }`}
              >
                {counts[tab.id]}
              </span>
            </button>
          )
        })}
      </div>

      {/* Tab Panel Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={active}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -10 }}
          transition={{ duration: 0.25, ease: 'easeOut' }}
        >
          {active === 'partial' && <PartialMatches matches={data.partial_matches} />}
          {active === 'exceptions' && <ExceptionsTable exceptions={data.exceptions} />}
          {active === 'matched' && <MatchedTable matches={data.matched} />}
          {active === 'audit' && <AuditTrail data={data} />}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
