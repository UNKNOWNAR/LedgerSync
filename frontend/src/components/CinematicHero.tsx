import { motion } from 'framer-motion'
import { ArrowDown, Cpu, ShieldCheck, Zap, Layers } from 'lucide-react'
import HeaderNav from './HeaderNav'
import FinancialCore3D from './FinancialCore3D'
import FloatingHUD from './FloatingHUD'

interface CinematicHeroProps {
  onLaunchClick?: () => void
}

export default function CinematicHero({ onLaunchClick }: CinematicHeroProps) {
  const scrollToApp = () => {
    if (onLaunchClick) {
      onLaunchClick()
    } else {
      const el = document.getElementById('reconciler-app')
      if (el) el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  const scrollToArchitecture = () => {
    const el = document.getElementById('architecture-pipeline')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="relative w-full min-h-screen bg-[#07090D] text-[#F5F7FA] overflow-hidden flex flex-col justify-between">
      {/* Top Header Navigation */}
      <HeaderNav onLaunchClick={scrollToApp} />

      {/* Ambient Radial Gradient Glows - Deep Financial Environment */}
      <div className="absolute top-1/4 left-1/2 -translate-x-1/2 w-[800px] h-[550px] bg-gradient-to-tr from-[#2F80FF]/15 via-[#00BFA6]/10 to-[#8B5CF6]/5 blur-[160px] pointer-events-none" />
      <div className="absolute bottom-10 left-10 w-[450px] h-[450px] bg-[#00BFA6]/5 blur-[130px] pointer-events-none" />

      {/* 0.2s Grid Pattern Background with Staggered Fade */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 0.35 }}
        transition={{ duration: 1.0, delay: 0.2 }}
        className="absolute inset-0 bg-grid-pattern pointer-events-none"
      />

      {/* Hero Body Content */}
      <div className="relative pt-24 pb-12 px-6 sm:px-12 max-w-7xl mx-auto w-full flex-1 flex flex-col justify-center items-center gap-8">

        {/* 1.3s Headline & Badge Group */}
        <div className="text-center space-y-4 max-w-3xl z-30">
          <motion.div
            initial={{ opacity: 0, y: -12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 1.2 }}
            className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-[#10141B]/95 border border-white/15 text-[0.72rem] font-mono text-[#4DA3FF] shadow-2xl backdrop-blur-md"
          >
            <span className="w-2 h-2 rounded-full bg-[#00BFA6] animate-ping" />
            <span className="text-[#8993A3]">Autonomous Financial Infrastructure ·</span>
            <span className="font-bold text-[#F5F7FA]">AI Reconciliation Core v1.0</span>
          </motion.div>

          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 1.3 }}
            className="text-4xl sm:text-6xl font-extrabold tracking-tight text-[#F5F7FA] leading-[1.1] font-sans"
          >
            Autonomous Financial Infrastructure for{' '}
            <span className="bg-gradient-to-r from-[#4DA3FF] to-[#60CFFF] bg-clip-text text-transparent">
              Real-Time Reconciliation
            </span>
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 1.4 }}
            className="text-sm sm:text-base text-[#8993A3] leading-relaxed max-w-2xl mx-auto"
          >
            Multi-tier deterministic matching, AI-powered exception resolution, and instant audit trail generation across heterogeneous ledger data streams.
          </motion.p>

          {/* 1.5s Action CTAs */}
          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.7, delay: 1.5 }}
            className="pt-2 flex flex-wrap items-center justify-center gap-4"
          >
            <motion.button
              onClick={scrollToApp}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="px-6 py-3.5 rounded-xl text-white font-semibold text-xs tracking-wide cursor-pointer flex items-center gap-2 transition-all relative overflow-hidden"
              style={{
                background: 'linear-gradient(135deg, #5BADFF 0%, #2F80FF 50%, #1A6AE8 100%)',
                boxShadow: '0 0 0 1px rgba(77,163,255,0.35), 0 4px 24px rgba(47,128,255,0.45), 0 1px 0 rgba(255,255,255,0.15) inset',
              }}
            >
              <Cpu size={16} />
              <span>Launch Reconciliation Engine</span>
              <span className="text-blue-200">→</span>
            </motion.button>

            <motion.button
              onClick={scrollToArchitecture}
              whileHover={{ scale: 1.03 }}
              whileTap={{ scale: 0.97 }}
              className="px-6 py-3.5 rounded-xl text-[#F5F7FA] font-semibold text-xs tracking-wide cursor-pointer flex items-center gap-2 transition-all"
              style={{
                background: 'rgba(255,255,255,0.04)',
                border: '1px solid rgba(255,255,255,0.14)',
                boxShadow: '0 1px 0 rgba(255,255,255,0.06) inset, 0 8px 24px rgba(0,0,0,0.3)',
              }}
            >
              <Layers size={15} className="text-[#8993A3]" />
              <span>Explore Architecture</span>
            </motion.button>
          </motion.div>
        </div>

        {/* 0.4s - 1.1s 3D WebGL Core Container with Overlaid Floating HUD */}
        <motion.div
          initial={{ opacity: 0, scale: 0.94 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.4 }}
          className="relative w-full max-w-5xl my-2"
        >
          {/* Ambient glow that grounds the canvas in the scene */}
          <div className="absolute -inset-4 rounded-[2rem] bg-gradient-to-b from-[#2F80FF]/10 via-[#00BFA6]/6 to-transparent blur-2xl pointer-events-none" />
          <div className="absolute -bottom-6 left-1/4 right-1/4 h-12 bg-[#2F80FF]/20 blur-2xl rounded-full pointer-events-none" />

          <div className="relative h-[460px] sm:h-[520px] rounded-3xl border border-[#2F80FF]/20 fintech-glass-panel overflow-hidden shadow-[0_0_60px_rgba(47,128,255,0.08),0_32px_64px_rgba(0,0,0,0.6)]">
            {/* 1.1s Overlaid Live Glassmorphism HUD Panels */}
            <FloatingHUD />

            {/* 0.4s-0.9s WebGL 3D Canvas Assembly */}
            <FinancialCore3D />
          </div>
        </motion.div>

        {/* Institutional Spec Cards Row */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, delay: 1.6 }}
          className="w-full max-w-5xl grid grid-cols-1 sm:grid-cols-3 gap-4 text-left z-30"
        >
          <div className="fintech-glass-panel p-4 rounded-xl border border-white/10 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#2F80FF]/15 border border-[#2F80FF]/30 flex items-center justify-center text-[#4DA3FF] shrink-0">
              <Zap size={16} />
            </div>
            <div>
              <div className="text-xs font-bold text-[#F5F7FA] font-mono">Sub-Second Processing</div>
              <div className="text-[0.68rem] text-[#8993A3] mt-0.5">Parses 50k+ ledger records in sub-second memory execution.</div>
            </div>
          </div>

          <div className="fintech-glass-panel p-4 rounded-xl border border-white/10 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#8B5CF6]/15 border border-[#8B5CF6]/30 flex items-center justify-center text-[#8B5CF6] shrink-0">
              <Cpu size={16} />
            </div>
            <div>
              <div className="text-xs font-bold text-[#F5F7FA] font-mono">Claude AI Exception Engine</div>
              <div className="text-[0.68rem] text-[#8993A3] mt-0.5">Autonomous natural language reasoning over fee & FX variances.</div>
            </div>
          </div>

          <div className="fintech-glass-panel p-4 rounded-xl border border-white/10 flex items-start gap-3">
            <div className="w-8 h-8 rounded-lg bg-[#00BFA6]/15 border border-[#00BFA6]/30 flex items-center justify-center text-[#00BFA6] shrink-0">
              <ShieldCheck size={16} />
            </div>
            <div>
              <div className="text-xs font-bold text-[#F5F7FA] font-mono">SOX / Audit Compliant</div>
              <div className="text-[0.68rem] text-[#8993A3] mt-0.5">Generates machine-readable JSONL ledgers & executive reports.</div>
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Scroll Indicator */}
      <div className="pb-6 flex justify-center items-center z-30">
        <button
          type="button"
          onClick={scrollToApp}
          className="flex flex-col items-center gap-1 text-[0.65rem] font-mono text-[#8993A3] hover:text-[#F5F7FA] transition-colors cursor-pointer"
        >
          <span>SCROLL TO CONTROLLER</span>
          <ArrowDown size={14} className="animate-bounce text-[#4DA3FF]" />
        </button>
      </div>
    </div>
  )
}
