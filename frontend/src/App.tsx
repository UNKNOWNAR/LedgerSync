import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Loader2, Play, AlertCircle, Cpu, Settings2 } from 'lucide-react'
import type { ReconcileConfig, ReconcileResponse } from './types'
import { startReconciliation, pollTaskStatus } from './api'
import CinematicHero from './components/CinematicHero'
import ArchitectureSection from './components/ArchitectureSection'
import FileUpload from './components/FileUpload'
import ConfigPanel from './components/ConfigPanel'
import MetricCards from './components/MetricCards'
import ResultsTabs from './components/ResultsTabs'
import DownloadSection from './components/DownloadSection'
import LiveEngineSection from './components/LiveEngineSection'
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

  const [pollingStatus, setPollingStatus] = useState<string | null>(null)

  const handleRun = useCallback(async () => {
    if (!gatewayFile || !bankFile) {
      setError('Please select both Payment Gateway and Bank Statement CSV files before executing.')
      return
    }
    
    const el = document.getElementById('backend-display-section')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
    
    setError(null)
    setData(null)
    setLoading(true)
    setPollingStatus("Dispatching to Celery worker...")
    
    try {
      const { task_id } = await startReconciliation(gatewayFile, bankFile, config)
      
      const poll = async () => {
        const status = await pollTaskStatus(task_id)
        setPollingStatus(status.status)
        
        if (status.state === "SUCCESS" && status.result) {
          setData(status.result)
          setLoading(false)
          setPollingStatus(null)
        } else if (status.state === "FAILURE") {
          throw new Error(status.status || "Celery task failed")
        } else {
          setTimeout(poll, 1000)
        }
      }
      
      poll()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Execution failed')
      setLoading(false)
      setPollingStatus(null)
    }
  }, [gatewayFile, bankFile, config])

  const scrollToApp = () => {
    const el = document.getElementById('reconciler-app')
    if (el) el.scrollIntoView({ behavior: 'smooth' })
  }

  return (
    <div className="min-h-screen w-full bg-[#080A0D] text-[#F5F7FA] font-sans relative selection:bg-[#2F80FF]/30">
      
      {/* Global Ambient White Hue */}
      <div className="fixed inset-0 pointer-events-none z-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-white/[0.03] via-transparent to-transparent" />
      <div className="fixed inset-0 pointer-events-none z-0 bg-[linear-gradient(to_bottom,_var(--tw-gradient-stops))] from-white/[0.01] to-transparent" />

      {/* Main Scrollable Content */}
      <div className="relative z-10">
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
                <span>{loading ? (pollingStatus || 'Processing...') : 'Run Reconciliation Engine'}</span>
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
                  className="rounded-2xl border border-white/[0.06] overflow-hidden"
                  style={{ background: 'linear-gradient(180deg, rgba(16,20,27,0.8) 0%, rgba(8,10,13,0.6) 100%)' }}
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                >
                  {/* Top bar */}
                  <div className="flex items-center justify-between px-5 py-3.5 border-b border-white/[0.06]">
                    <div className="flex items-center gap-2">
                      <div className="w-2 h-2 rounded-full bg-[#2F80FF]/50 animate-pulse" />
                      <span className="text-[0.65rem] font-mono text-[#4A5568] uppercase tracking-widest">Awaiting Ledger Input</span>
                    </div>
                    <span className="text-[0.6rem] font-mono text-[#2A3140] uppercase tracking-widest">0 records loaded</span>
                  </div>

                  {/* Fake shimmer rows */}
                  <div className="px-5 py-4 space-y-2.5">
                    {[...Array(5)].map((_, i) => (
                      <div key={i} className="flex items-center gap-3 opacity-30" style={{ opacity: 0.15 + i * 0.05 }}>
                        <div className="h-3 rounded-md bg-white/10" style={{ width: `${60 + (i * 17) % 40}px` }} />
                        <div className="h-3 rounded-md bg-white/10 flex-1" />
                        <div className="h-3 rounded-md bg-white/10 w-16" />
                        <div className="h-3 rounded-md bg-white/10 w-20" />
                        <div className="h-5 rounded-full bg-white/5 w-14" />
                      </div>
                    ))}
                  </div>

                  {/* CTA inside */}
                  <div className="flex flex-col items-center gap-3 py-8 border-t border-white/[0.04]">
                    <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: 'rgba(47,128,255,0.08)', border: '1px solid rgba(47,128,255,0.15)' }}>
                      <Play size={18} className="text-[#4DA3FF] ml-0.5" />
                    </div>
                    <div className="space-y-1 text-center">
                      <p className="text-sm font-semibold text-[#F5F7FA]">Ready to Reconcile</p>
                      <p className="text-xs text-[#4A5568] max-w-xs mx-auto leading-relaxed">
                        Upload both CSV ledgers above, then hit <span className="text-[#4DA3FF] font-medium">Run Reconciliation Engine</span> to begin.
                      </p>
                    </div>
                  </div>
                </motion.div>
              ) : null}
            </AnimatePresence>
          </div>
        </div>
      </section>

      {/* 4. Live Reconciliation Engine Visualization (Moved to bottom) */}
      <LiveEngineSection data={data} isProcessing={loading} />

      {/* Footer */}
      <footer className="py-6 px-8 border-t border-white/[0.06] bg-[#080A0D]">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-2 h-2 rounded-full bg-[#00BFA6] animate-pulse" />
            <span className="text-[0.65rem] font-mono text-[#3A4454] uppercase tracking-widest">All Systems Operational</span>
          </div>
          <span className="text-[0.65rem] font-mono text-[#2A3140] uppercase tracking-widest">
            LedgerSync v1.0 &nbsp;·&nbsp; Powered by Autonomous LLM Engine
          </span>
          <div className="flex items-center gap-4">
            <span className="text-[0.65rem] font-mono text-[#2A3140]">SOX Compliant</span>
            <span className="text-[0.65rem] font-mono text-[#2A3140]">AES-256</span>
            <span className="text-[0.65rem] font-mono text-[#2A3140]">ISO 27001</span>
          </div>
        </div>
      </footer>
      </div>
    </div>
  )
}
