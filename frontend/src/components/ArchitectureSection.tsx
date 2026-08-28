import { motion } from 'framer-motion'
import { FileSpreadsheet, Database, Target, GitCompare, Cpu, FileCheck } from 'lucide-react'

const pipelineStages = [
  {
    step: '01',
    title: 'Ingestion & Cleaning',
    subtitle: 'Payment Gateway CSV & Bank Statement CSV',
    icon: FileSpreadsheet,
    badge: 'Raw Ingestion',
    color: 'text-[#4DA3FF]',
    borderColor: 'border-[#2F80FF]/30',
    bgColor: 'bg-[#2F80FF]/10',
    description: 'Parses heterogeneous gateway and bank settlement CSVs. Normalizes date strings, strips currency symbols, and validates column encodings.',
    metrics: ['UTF-8 Encoding', 'ISO-8601 Dates', 'Row Sanitization'],
  },
  {
    step: '02',
    title: 'Tier 1 — Exact Matching',
    subtitle: 'Deterministic Reference Resolution',
    icon: Target,
    badge: 'O(1) Resolution',
    color: 'text-[#00BFA6]',
    borderColor: 'border-[#00BFA6]/30',
    bgColor: 'bg-[#00BFA6]/10',
    description: 'Performs instant hash-map lookups on exact transaction IDs, reference numbers, and 100% identical dollar amounts.',
    metrics: ['Instant Hash Match', 'Zero False Positives', 'Primary Ledger'],
  },
  {
    step: '03',
    title: 'Tier 2 — Fuzzy Rule Matching',
    subtitle: 'Heuristic Similarity Engine',
    icon: GitCompare,
    badge: 'Configurable Rules',
    color: 'text-[#F59E0B]',
    borderColor: 'border-[#F59E0B]/30',
    bgColor: 'bg-[#F59E0B]/10',
    description: 'Evaluates candidate matches across flexible windows: settlement date gap tolerance (±N days), amount variance %, and merchant string edit distance.',
    metrics: ['Settlement Window', 'Fee Variance %', 'Levenshtein Distance'],
  },
  {
    step: '04',
    title: 'Tier 3 — Deep LLM Exception Reasoning',
    subtitle: 'LLM Multi-Record Discrepancy Analysis',
    icon: Cpu,
    badge: 'Autonomous AI',
    color: 'text-[#8B5CF6]',
    borderColor: 'border-[#8B5CF6]/30',
    bgColor: 'bg-[#8B5CF6]/10',
    description: 'Deploys an advanced Large Language Model to reason over unresolved edge cases, interchange fee rollups, partial payouts, and complex multi-record splits.',
    metrics: ['Confidence Score', 'Natural Language Rationale', 'Edge-Case Resolution'],
  },
  {
    step: '05',
    title: 'Auditable Financial Ledger',
    subtitle: 'Immutable Report & Compliance Artifacts',
    icon: FileCheck,
    badge: 'Export Ready',
    color: 'text-[#F5F7FA]',
    borderColor: 'border-white/20',
    bgColor: 'bg-white/10',
    description: 'Writes machine-readable audit trail JSONL ledgers, matched records CSVs, exceptions CSVs, and executive markdown summary reports.',
    metrics: ['matched.csv', 'exceptions.csv', 'audit_trail.jsonl'],
  },
]

export default function ArchitectureSection() {
  return (
    <section id="architecture-pipeline" className="py-24 px-6 sm:px-12 max-w-6xl mx-auto space-y-16">
      {/* Section Title */}
      <div className="text-center space-y-4 max-w-2xl mx-auto">
        <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[#2F80FF]/10 border border-[#2F80FF]/25 text-[#4DA3FF] text-[0.72rem] font-mono uppercase tracking-wider">
          <Database size={12} />
          <span>Core Reconciliation Pipeline</span>
        </div>

        <h2 className="text-3xl sm:text-4xl font-bold tracking-tight text-[#F5F7FA]">
          Institutional Multi-Tier Matching Engine
        </h2>

        <p className="text-sm text-[#8993A3] leading-relaxed">
          From raw CSV ingestion to automated LLM exception reasoning, every transaction passes through five deterministic and heuristic matching layers.
        </p>
      </div>

      {/* Pipeline Grid Cards */}
      <div className="relative space-y-6">
        {/* Flow Line Connector */}
        <div className="hidden lg:block absolute left-1/2 top-8 bottom-8 w-[2px] bg-gradient-to-b from-[#2F80FF] via-[#8B5CF6] to-[#00BFA6] opacity-35 -translate-x-1/2" />

        {pipelineStages.map((stage, index) => {
          const Icon = stage.icon
          const isEven = index % 2 === 0

          return (
            <motion.div
              key={stage.step}
              initial={{ opacity: 0, y: 24 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true, margin: '-50px' }}
              transition={{ duration: 0.5, delay: index * 0.1 }}
              className={`flex flex-col lg:flex-row items-center gap-8 ${
                isEven ? 'lg:flex-row' : 'lg:flex-row-reverse'
              }`}
            >
              {/* Card content */}
              <div className="w-full lg:w-1/2 fintech-glass-panel p-6 sm:p-8 rounded-2xl border border-white/10 space-y-4 relative overflow-hidden group hover:border-white/20 transition-all">
                {/* Subtle Glow Accent */}
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/10 to-transparent" />

                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl ${stage.bgColor} border ${stage.borderColor} flex items-center justify-center ${stage.color}`}>
                      <Icon size={20} />
                    </div>
                    <div>
                      <div className="text-[0.68rem] font-mono text-[#8993A3] tracking-wider uppercase">Stage {stage.step}</div>
                      <h3 className="text-lg font-bold text-[#F5F7FA] tracking-tight">{stage.title}</h3>
                    </div>
                  </div>

                  <span className={`text-[0.65rem] font-mono font-medium px-2.5 py-1 rounded ${stage.bgColor} ${stage.color} border ${stage.borderColor}`}>
                    {stage.badge}
                  </span>
                </div>

                <p className="text-xs text-[#8993A3] leading-relaxed">
                  {stage.description}
                </p>

                {/* Technical Metadata Pills */}
                <div className="pt-2 flex flex-wrap gap-2">
                  {stage.metrics.map((m) => (
                    <span key={m} className="px-2 py-0.5 rounded bg-white/[0.04] border border-white/10 text-[0.65rem] font-mono text-[#8993A3]">
                      {m}
                    </span>
                  ))}
                </div>
              </div>

              {/* Center Node Indicator */}
              <div className="hidden lg:flex w-10 h-10 rounded-full bg-[#10141B] border border-white/20 items-center justify-center z-10 text-xs font-mono font-bold text-[#4DA3FF] shadow-xl">
                {stage.step}
              </div>

              {/* Empty Spacer Column for Desktop Grid */}
              <div className="hidden lg:block w-1/2" />
            </motion.div>
          )
        })}
      </div>
    </section>
  )
}
