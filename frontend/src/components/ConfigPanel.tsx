import { motion } from 'framer-motion'
import { Sliders, Sparkles } from 'lucide-react'
import type { ReconcileConfig } from '../types'

interface ConfigPanelProps {
  config: ReconcileConfig
  onChange: (config: ReconcileConfig) => void
}

function SliderGroup({
  label,
  value,
  min,
  max,
  step,
  unit,
  description,
  onChange,
}: {
  label: string
  value: number
  min: number
  max: number
  step: number
  unit?: string
  description?: string
  onChange: (v: number) => void
}) {
  return (
    <div className="space-y-2 mb-6">
      <div className="flex justify-between items-center text-xs">
        <span className="font-medium text-[#F5F7FA]">{label}</span>
        <span className="font-mono text-xs text-[#4DA3FF] font-semibold px-2 py-0.5 rounded bg-[#2F80FF]/10 border border-[#2F80FF]/20">
          {value}{unit}
        </span>
      </div>
      {description && <p className="text-[0.7rem] text-[#8993A3] font-normal leading-normal">{description}</p>}
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full h-1.5 bg-[#2F80FF]/20 rounded-lg appearance-none cursor-pointer accent-[#4DA3FF]"
      />
    </div>
  )
}

export default function ConfigPanel({ config, onChange }: ConfigPanelProps) {
  const set = (patch: Partial<ReconcileConfig>) => onChange({ ...config, ...patch })

  return (
    <aside className="w-80 shrink-0 h-full border-r border-white/[0.08] bg-[#10141B]/60 backdrop-blur-xl p-6 overflow-y-auto flex flex-col justify-between select-none">
      <div className="space-y-6">
        {/* Sidebar Header */}
        <div className="flex items-center gap-3 pb-6 border-b border-white/10">
          <div className="w-9 h-9 rounded-xl bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
            <Sliders size={18} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-[#F5F7FA]">Rules & Config</h2>
            <p className="text-xs text-[#8993A3]">Matching Thresholds</p>
          </div>
        </div>

        {/* Form Controls */}
        <div>
          <SliderGroup
            label="Settlement Window"
            description="Max allowed days between Gateway & Bank"
            value={config.date_gap_days}
            min={1}
            max={7}
            step={1}
            unit=" days"
            onChange={(v) => set({ date_gap_days: v })}
          />

          <SliderGroup
            label="Amount Variance"
            description="Fee/fx tolerance percentage"
            value={config.amount_variance_pct}
            min={0.5}
            max={10}
            step={0.5}
            unit="%"
            onChange={(v) => set({ amount_variance_pct: v })}
          />

          <SliderGroup
            label="String Similarity"
            description="Fuzzy merchant name match threshold"
            value={config.merchant_similarity_threshold}
            min={60}
            max={100}
            step={5}
            unit="%"
            onChange={(v) => set({ merchant_similarity_threshold: v })}
          />

          {/* AI Reasoning Switch */}
          <div className="p-4 rounded-xl bg-white/[0.03] border border-white/10 space-y-3 mt-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <Sparkles size={16} className="text-[#8B5CF6]" />
                <span className="text-xs font-medium text-[#F5F7FA]">LLM Reasoning</span>
              </div>
              <button
                type="button"
                role="switch"
                aria-checked={config.llm_enabled}
                onClick={() => set({ llm_enabled: !config.llm_enabled })}
                className="relative w-11 h-6 rounded-full transition-colors duration-200 p-0.5"
                style={{
                  background: config.llm_enabled ? '#2563eb' : 'rgba(255, 255, 255, 0.15)',
                }}
              >
                <motion.div
                  className="w-5 h-5 rounded-full bg-white shadow-sm"
                  animate={{ x: config.llm_enabled ? 20 : 0 }}
                  transition={{ type: 'spring', stiffness: 500, damping: 30 }}
                />
              </button>
            </div>
            <p className="text-[0.7rem] text-[#8993A3] leading-relaxed">
              Enables deep LLM analysis for complex discrepancy edge-cases.
            </p>
          </div>
        </div>
      </div>

      {/* Footer Info */}
      <div className="pt-6 border-t border-white/10 flex items-center justify-between text-xs text-zinc-400">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
          <span>FastAPI Engine</span>
        </div>
        <span className="font-mono text-[0.7rem] text-[#8993A3]">v1.2.0</span>
      </div>
    </aside>
  )
}
