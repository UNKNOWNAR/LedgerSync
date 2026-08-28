import { useState, useRef, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { ArrowDown, Cpu, Layers } from 'lucide-react'
import Spline from '@splinetool/react-spline'
import HeaderNav from './HeaderNav'

interface CinematicHeroProps {
  onLaunchClick?: () => void
}

export default function CinematicHero({ onLaunchClick }: CinematicHeroProps) {
  const [splineLoaded, setSplineLoaded] = useState(false)
  const splineContainerRef = useRef<HTMLDivElement>(null)

  // Intercept wheel events in capture phase before they reach the Spline canvas
  // This prevents Spline's built-in scroll-to-zoom while keeping page scroll intact
  useEffect(() => {
    const el = splineContainerRef.current
    if (!el) return
    const stopWheelZoom = (e: WheelEvent) => e.stopPropagation()
    el.addEventListener('wheel', stopWheelZoom, { capture: true, passive: true })
    return () => el.removeEventListener('wheel', stopWheelZoom, { capture: true })
  }, [])

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
    <div className="w-full flex flex-col">
      {/* ─── SECTION 1: SPLINE HERO ─── */}
      <div className="relative w-full min-h-screen bg-transparent text-[#F5F7FA] overflow-hidden flex flex-col justify-between">
        
        {/* Dynamic Background Spline */}
        <motion.div
          ref={splineContainerRef}
          initial={{ opacity: 0, scale: 1.05 }}
          animate={{ opacity: 0.55, scale: 1 }}
          transition={{ duration: 1.8, ease: [0.16, 1, 0.3, 1] }}
          className="absolute inset-0 z-0 pointer-events-auto"
        >
          <Spline
            scene="/scene.splinecode"
            className="w-full h-full mix-blend-luminosity"
            onLoad={() => {
              // Wait 4.5 seconds for the Spline cards to completely finish their intro animation
              setTimeout(() => setSplineLoaded(true), 4500)
            }}
          />
          {/* Multi-layer darkening: corners, centre, and bottom fade */}
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_transparent_30%,_rgba(8,10,13,0.7)_100%)]" style={{ pointerEvents: 'none' }} />
          <div className="absolute inset-0 bg-gradient-to-b from-[#080A0D]/40 via-transparent to-[#080A0D]" style={{ pointerEvents: 'none' }} />
          <div className="absolute inset-0 bg-gradient-to-t from-transparent via-transparent to-[#080A0D]/60" style={{ pointerEvents: 'none' }} />
        </motion.div>

        <AnimatePresence>
          {splineLoaded && (
            <>
              {/* Top Header Navigation */}
              <motion.div
                key="header"
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.8 }}
                className="relative z-50 pointer-events-auto"
              >
                <HeaderNav onLaunchClick={scrollToApp} />
              </motion.div>

              {/* Hero Body Content */}
              <motion.div 
                key="body"
                className="relative z-30 pt-12 pb-12 px-6 sm:px-12 max-w-5xl mx-auto w-full flex-1 flex flex-col justify-center items-center gap-8 pointer-events-none"
              >
                <div className="text-center space-y-6 max-w-3xl pointer-events-auto">
                  
                  <motion.div
                    initial={{ opacity: 0, y: -12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.5, delay: 0.1 }}
                    className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-[#10141B]/80 border border-white/[0.08] text-[0.75rem] font-medium text-[#4DA3FF] shadow-[0_4px_24px_rgba(0,0,0,0.4),inset_0_1px_1px_rgba(255,255,255,0.1)] backdrop-blur-xl"
                  >
              <span className="w-1.5 h-1.5 rounded-full bg-[#00BFA6] animate-pulse" />
              <span className="text-[#8993A3] font-sans">Autonomous Financial Infrastructure <span className="opacity-50 mx-1">·</span></span>
              <span className="font-semibold text-[#F5F7FA] font-sans tracking-wide">AI Reconciliation Core <span className="font-mono text-[0.65rem] text-[#4DA3FF] ml-1 bg-[#2F80FF]/15 px-1.5 py-0.5 rounded-md">v1.0</span></span>
            </motion.div>

                  <motion.h1
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7, delay: 0.3 }}
                    className="text-4xl sm:text-6xl sm:leading-[1.1] font-extrabold tracking-tight text-[#F5F7FA] leading-tight font-sans drop-shadow-2xl"
                  >          Autonomous Financial Infrastructure for{' '}
              <span className="bg-gradient-to-r from-[#4DA3FF] to-[#60CFFF] bg-clip-text text-transparent">
                Real-Time Reconciliation
              </span>
            </motion.h1>

            <motion.p
              initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7, delay: 0.5 }}
                    className="text-sm sm:text-base text-[#E2E8F0] leading-relaxed max-w-2xl mx-auto drop-shadow-md font-medium"
                  >
                    Multi-tier deterministic matching, AI-powered exception resolution, and instant audit trail generation across heterogeneous ledger data streams.
                  </motion.p>

                  {/* Action CTAs */}
                  <motion.div
                    initial={{ opacity: 0, y: 16 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.7, delay: 0.7 }}
                    className="pt-4 flex flex-wrap items-center justify-center gap-4"
                  >
                    <motion.button
                      onClick={scrollToApp}
                      whileHover={{ scale: 1.03 }}
                      whileTap={{ scale: 0.97 }}
                      className="px-6 py-3.5 rounded-xl text-white font-semibold text-xs tracking-wide cursor-pointer flex items-center gap-2 transition-all relative overflow-hidden"
                      style={{
                        background: '#2F80FF',
                        boxShadow: '0 8px 32px rgba(47,128,255,0.25), inset 0 1px 1px rgba(255,255,255,0.2)',
                        border: '1px solid rgba(77,163,255,0.4)',
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
                      className="px-6 py-3.5 rounded-xl text-[#F5F7FA] font-semibold text-xs tracking-wide cursor-pointer flex items-center gap-2 transition-all backdrop-blur-md"
                      style={{
                        background: 'rgba(255,255,255,0.06)',
                        border: '1px solid rgba(255,255,255,0.15)',
                        boxShadow: '0 1px 0 rgba(255,255,255,0.06) inset, 0 8px 24px rgba(0,0,0,0.4)',
                      }}
                    >
                      <Layers size={15} className="text-[#A0ABC0]" />
                      <span>Explore Architecture</span>
                    </motion.button>
                  </motion.div>
                </div>
              </motion.div>

              {/* Bottom Scroll Indicator */}
              <motion.div
                key="scroll-indicator"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 1.0, delay: 1.0 }}
                className="relative z-30 pb-8 flex justify-center items-center pointer-events-auto"
              >
                <button
                  type="button"
                  onClick={() => {
                    const el = document.getElementById('backend-display-section')
                    if (el) el.scrollIntoView({ behavior: 'smooth' })
                  }}
                  className="flex flex-col items-center gap-2 text-[0.65rem] font-mono text-[#A0ABC0] hover:text-[#F5F7FA] transition-colors cursor-pointer"
                >
                  <span>SCROLL TO LIVE ENGINE</span>
                  <ArrowDown size={14} className="animate-bounce text-[#4DA3FF]" />
                </button>
              </motion.div>
            </>
          )}
        </AnimatePresence>
      </div>


    </div>
  )
}
