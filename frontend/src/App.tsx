import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Play, AlertCircle, Cpu, Settings2 } from 'lucide-react'
import type { ReconcileConfig, ReconcileResponse } from './types'
import { reconcile } from './api'
import CinematicHero from './components/CinematicHero'
import ArchitectureSection from './components/ArchitectureSection'
import FileUpload from './components/FileUpload'
import ConfigPanel from './components/ConfigPanel'
import MetricCards from './components/MetricCards'
import ResultsTabs from './components/ResultsTabs'
import DownloadSection from './components/DownloadSection'
import { useLenis } from './hooks/useLenis'

export default function App() {
  const [config, setConfig] = useState<ReconcileConfig>({
    date_gap_days: 3,
    amount_variance_pct: 2.0,
    merchant_similarity_threshold: 80,
    llm_enabled: false,
  })

  const [gatewayFile, setGatewayFile] = useState<File | null>(null)
  const [bankFile, setBankFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [data, setData] = useState<ReconcileResponse | null>(null)
  const [showMobileConfig, setShowMobileConfig] = useState(false)

  useLenis()

  const handleRun = useCallback(async () => {
    if (!gatewayFile || !bankFile) {
      setError('Please select both Payment Gateway and Bank Statement CSV files before executing.')
      return
    }
    setError(null)
    setLoading(true)
    try {
      const result = await reconcile(gatewayFile, bankFile, config)
      setData(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed')
    } finally {
      setLoading(false)
    }
  }, [gatewayFile, bankFile, config])

  const scrollToApp = () => {
    const el = document.getElementById('reconciler-app')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen w-full bg-[#080A0D] text-[#F5F7FA] font-sans relative selection:bg-[#2F80FF]/30">
      {/* 1. Cinematic 3D WebGL Landing Hero Section */}
      <CinematicHero onLaunchClick={scrollToApp} />

      {/* 2. Core Architecture Pipeline Breakdown Section */}
      <ArchitectureSection />

      {/* 3. Main Reconciliation Application Section */}
      <section id="reconciler-app" className="py-16 px-6 sm:px-12 max-w-7xl mx-auto space-y-12">
        {/* Section Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-white/10 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-[#2F80FF]/15 border border-[#2F80FF]/30 flex items-center justify-center text-[#4DA3FF]">
                <Cpu size={15} />
              </div>
              <span className="text-xs font-mono uppercase text-[#4DA3FF] tracking-wider font-semibold">
                Reconciliation Workspace
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#F5F7FA]">
              Execute Financial Reconciliation
            </h2>
            <p className="text-xs sm:text-sm text-[#8D96A5]">
              Upload Payment Gateway and Bank Settlement CSV ledgers to run multi-tier matching.
            </p>
          </div>

          <button
            type="button"
            onClick={() => setShowMobileConfig(!showMobileConfig)}
            className="lg:hidden px-4 py-2 rounded-xl bg-[#101318] border border-white/15 text-xs font-medium text-[#F5F7FA] flex items-center gap-2"
          >
            <Settings2 size={15} />
            <span>Config Parameters</span>
          </button>
        </div>

        {/* 2-Column Application Layout: Left Config + Right Execution Workspace */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
          {/* Config Sidebar (Desktop Always, Mobile Toggle) */}
          <div className={`lg:col-span-4 ${showMobileConfig ? 'block' : 'hidden lg:block'} sticky top-20`}>
            <ConfigPanel config={config} onChange={setConfig} />
          </div>

          {/* Main Execution & Output Area */}
          <div className="lg:col-span-8 space-y-8">
            {/* File Upload Section */}
            <FileUpload
              gatewayFile={gatewayFile}
              bankFile={bankFile}
              onGatewayFile={setGatewayFile}
              onBankFile={setBankFile}
            />

            {/* Run Action CTA Button */}
            <div className="space-y-3">
              <motion.button
                onClick={handleRun}
                disabled={loading}
                className="w-full py-4 bg-[#2F80FF] hover:bg-[#4DA3FF] active:scale-[0.99] text-white font-semibold rounded-xl shadow-xl shadow-[#2F80FF]/25 transition-all flex items-center justify-center gap-2 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-sm border border-blue-400/30"
                whileTap={{ scale: 0.99 }}
              >
                {loading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Play size={16} fill="currentColor" />
                )}
                <span>{loading ? 'Processing Reconciliation Pipelines...' : 'Run Reconciliation Engine'}</span>
              </motion.button>

              <AnimatePresence>
                {error && (
                  <motion.div
                    className="flex items-center gap-2 text-xs text-rose-400 bg-rose-500/10 p-3.5 rounded-xl border border-rose-500/20"
                    initial={{ opacity: 0, y: -4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, y: -4 }}
                  >
                    <AlertCircle size={16} className="shrink-0" />
                    <span>{error}</span>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Reconciliation Output Results */}
            <AnimatePresence mode="wait">
              {data ? (
                <motion.div
                  key="results"
                  initial={{ opacity: 0, y: 16 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
                  className="space-y-8"
                >
                  <MetricCards metrics={data.metrics} />
                  <ResultsTabs data={data} />
                  <DownloadSection runId={data.run_id} />
                </motion.div>
              ) : !loading ? (
                <motion.div
                  key="empty-state"
                  className="py-20 text-center rounded-2xl border border-white/[0.08] backdrop-blur-md flex flex-col items-center gap-5"
                  style={{ background: 'linear-gradient(180deg, rgba(16,20,27,0.7) 0%, rgba(10,13,18,0.5) 100%)' }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{ background: 'rgba(47,128,255,0.08)', border: '1px solid rgba(47,128,255,0.18)', boxShadow: '0 0 32px rgba(47,128,255,0.08)' }}>
                    <Play size={22} className="text-[#4DA3FF] ml-0.5" />
                  </div>
                  <div className="space-y-1.5">
                    <p className="text-sm font-semibold text-[#F5F7FA]">Ready to Reconcile</p>
                    <p className="text-xs text-[#5A6474] max-w-xs mx-auto leading-relaxed">
                      Upload both CSV ledgers and click <span className="text-[#8993A3] font-medium">Run Reconciliation Engine</span> to begin multi-tier matching.
                    </p>
                  </div>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-white/10 text-center text-xs font-mono text-[#8D96A5]">
        AI FINANCE CONTROLLER v1.0 · Institutional Financial Infrastructure · Powered by Claude AI Engine
      </footer>
    </div>
  )
}
