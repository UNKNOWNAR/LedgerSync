import { motion } from 'framer-motion'
import { FileText, FileSpreadsheet, Code } from 'lucide-react'
import { getReportUrl } from '../api'
import Card3D from './Card3D'

const reports = [
  { key: 'exceptions_csv', label: 'Exceptions Report', filename: 'exceptions.csv', icon: FileSpreadsheet, type: 'CSV Format' },
  { key: 'exception_report_md', label: 'Executive Summary', filename: 'exception_report.md', icon: FileText, type: 'Markdown Report' },
  { key: 'audit_trail_jsonl', label: 'Audit Trail Ledger', filename: 'audit_trail.jsonl', icon: Code, type: 'JSONL Audit File' },
  { key: 'matched_csv', label: 'Matched Records', filename: 'matched.csv', icon: FileSpreadsheet, type: 'CSV Format' },
]

export default function DownloadSection({ runId }: { runId: string }) {
  return (
    <div className="pt-8 pb-12 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-semibold tracking-[0.08em] text-zinc-400 uppercase flex items-center gap-2">
          <span>Exported Financial Artifacts</span>
          <span className="text-[0.65rem] px-2 py-0.5 rounded bg-blue-500/10 border border-blue-500/20 text-blue-400">3D Interactive</span>
        </h3>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {reports.map((report, i) => {
          const Icon = report.icon
          return (
            <motion.div
              key={report.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.05, duration: 0.4 }}
            >
              <Card3D intensity={10}>
                <a
                  href={getReportUrl(runId, report.key)}
                  download={report.filename}
                  className="flex items-center gap-3.5 p-4 rounded-2xl border no-underline group select-none transition-colors block"
                  style={{
                    background: 'rgba(255, 255, 255, 0.03)',
                    borderColor: 'rgba(255, 255, 255, 0.08)',
                    backdropFilter: 'blur(16px)',
                    transformStyle: 'preserve-3d',
                  }}
                >
                  <div
                    className="w-10 h-10 rounded-xl bg-white/[0.06] border border-white/10 flex items-center justify-center shrink-0 group-hover:bg-[#0071e3] group-hover:border-[#0071e3] transition-colors"
                    style={{ transform: 'translateZ(12px)' }}
                  >
                    <Icon size={18} className="text-zinc-300 group-hover:text-white transition-colors" />
                  </div>
                  <div className="min-w-0" style={{ transform: 'translateZ(8px)' }}>
                    <div className="text-xs font-semibold text-zinc-100 truncate">{report.label}</div>
                    <div className="text-[0.68rem] text-zinc-400 font-mono mt-0.5 truncate">{report.filename}</div>
                  </div>
                </a>
              </Card3D>
            </motion.div>
          )
        })}
      </div>
    </div>
  )
}
