import { motion } from 'framer-motion'
import { ArrowUpRight, Cpu } from 'lucide-react'

interface HeaderNavProps {
  onLaunchClick?: () => void
}

export default function HeaderNav({ onLaunchClick }: HeaderNavProps) {
  const scrollToSection = (id: string) => {
    const el = document.getElementById(id)
    if (el) {
      el.scrollIntoView({ behavior: 'smooth' })
    }
  }

  return (
    <header className="fixed top-0 left-0 right-0 h-16 z-50 bg-[#080A0D]/80 backdrop-blur-xl border-b border-white/[0.08] px-6 sm:px-12 flex items-center justify-between transition-all">
      {/* LEFT: Logo */}
      <div className="flex items-center gap-3 select-none">
        <div className="w-8 h-8 rounded-lg bg-[#2F80FF]/10 border border-[#2F80FF]/30 flex items-center justify-center text-[#2F80FF]">
          <Cpu size={16} />
        </div>
        <div className="flex items-center gap-2">
          <span className="font-bold text-xs tracking-[0.15em] text-[#F5F7FA] uppercase font-mono">
            AI Finance Controller
          </span>
          <span className="inline-flex items-center px-1.5 py-0.5 rounded text-[0.62rem] font-mono font-medium bg-[#2F80FF]/15 text-[#4DA3FF] border border-[#2F80FF]/25">
            v1.0
          </span>
        </div>
      </div>

      {/* CENTER/RIGHT: Nav Links */}
      <nav className="hidden md:flex items-center gap-8 text-xs font-medium text-[#8D96A5]">
        <button
          type="button"
          onClick={() => scrollToSection('product-overview')}
          className="hover:text-[#F5F7FA] transition-colors cursor-pointer"
        >
          Product
        </button>
        <button
          type="button"
          onClick={() => scrollToSection('architecture-pipeline')}
          className="hover:text-[#F5F7FA] transition-colors cursor-pointer"
        >
          Architecture
        </button>

        <a
          href="https://github.com"
          target="_blank"
          rel="noreferrer"
          className="hover:text-[#F5F7FA] transition-colors inline-flex items-center gap-1"
        >
          <span>GitHub</span>
          <ArrowUpRight size={11} className="opacity-70" />
        </a>
      </nav>

      {/* RIGHT: Launch Controller CTA */}
      <div className="flex items-center gap-4">
        <motion.button
          onClick={() => {
            if (onLaunchClick) onLaunchClick()
            else scrollToSection('reconciler-app')
          }}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className="px-4 py-2 rounded-lg bg-[#2F80FF] hover:bg-[#4DA3FF] text-white text-xs font-semibold tracking-wide shadow-lg shadow-[#2F80FF]/20 border border-blue-400/30 transition-all cursor-pointer flex items-center gap-1.5"
        >
          <span>Launch Controller</span>
          <span className="text-blue-200">→</span>
        </motion.button>
      </div>
    </header>
  )
}
