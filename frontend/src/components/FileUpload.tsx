import { motion, AnimatePresence } from 'framer-motion'
import { Upload, CheckCircle2, X } from 'lucide-react'
import { useCallback, useState, useRef } from 'react'
import Card3D from './Card3D'

interface FileUploadProps {
  label: string
  description: string
  file: File | null
  onFile: (file: File | null) => void
  delay?: number
}

function FileUploadCard({ label, description, file, onFile, delay = 0 }: FileUploadProps) {
  const [dragging, setDragging] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragging(false)
      const f = e.dataTransfer.files[0]
      if (f && f.name.endsWith('.csv')) onFile(f)
    },
    [onFile],
  )

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const f = e.target.files?.[0]
      if (f) onFile(f)
    },
    [onFile],
  )

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: delay * 0.08, duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
      className="space-y-2"
    >
      <div>
        <div className="text-xs font-semibold text-zinc-200 tracking-tight">{label}</div>
        <div className="text-[0.7rem] text-zinc-400 font-mono mt-0.5">{description}</div>
      </div>

      <Card3D intensity={12}>
        <div
          className={`p-8 rounded-2xl border border-dashed transition-all flex flex-col items-center justify-center text-center cursor-pointer select-none relative ${
            dragging
              ? 'border-blue-500 bg-blue-500/10 shadow-lg shadow-blue-500/20'
              : file
              ? 'border-emerald-500/40 bg-emerald-500/[0.03] shadow-lg shadow-emerald-500/10'
              : 'border-white/15 bg-white/[0.02] hover:bg-white/[0.04]'
          }`}
          style={{ transformStyle: 'preserve-3d' }}
          onDragOver={(e) => {
            e.preventDefault()
            setDragging(true)
          }}
          onDragLeave={() => setDragging(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept=".csv"
            className="hidden"
            onChange={handleChange}
          />

          <AnimatePresence mode="wait">
            {file ? (
              <motion.div
                key="file-active"
                className="flex items-center justify-between w-full"
                style={{ transform: 'translateZ(16px)' }}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                transition={{ duration: 0.2 }}
              >
                <div className="flex items-center gap-3 min-w-0 text-left">
                  <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center shrink-0">
                    <CheckCircle2 size={20} className="text-emerald-400" />
                  </div>
                  <div className="min-w-0">
                    <p className="text-xs font-semibold text-zinc-100 truncate">{file.name}</p>
                    <p className="text-[0.68rem] text-zinc-400 font-mono mt-0.5">
                      {(file.size / 1024).toFixed(1)} KB · Ready
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={(e) => {
                    e.stopPropagation()
                    onFile(null)
                  }}
                  className="w-7 h-7 rounded-lg bg-white/[0.06] hover:bg-white/[0.12] text-zinc-400 hover:text-white flex items-center justify-center transition-colors"
                  title="Remove file"
                >
                  <X size={14} />
                </button>
              </motion.div>
            ) : (
              <motion.div
                key="file-empty"
                className="flex flex-col items-center justify-center text-center space-y-2 py-2"
                style={{ transform: 'translateZ(16px)' }}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
              >
                <div className="w-10 h-10 rounded-xl bg-white/[0.04] border border-white/[0.08] flex items-center justify-center text-zinc-400 transition-colors">
                  <Upload size={18} strokeWidth={1.75} />
                </div>
                <div>
                  <p className="text-xs font-medium text-zinc-300">
                    Drop CSV file here or <span className="text-blue-400">browse</span>
                  </p>
                  <p className="text-[0.68rem] text-zinc-400 mt-0.5">Supports UTF-8 formatted CSV</p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </Card3D>
    </motion.div>
  )
}

interface FileUploadSectionProps {
  gatewayFile: File | null
  bankFile: File | null
  onGatewayFile: (f: File | null) => void
  onBankFile: (f: File | null) => void
}

export default function FileUpload({
  gatewayFile,
  bankFile,
  onGatewayFile,
  onBankFile,
}: FileUploadSectionProps) {
  return (
    <div className="grid grid-cols-2 gap-6">
      <FileUploadCard
        label="Payment Gateway Export"
        description="transaction_id, amount, date, merchant_name, reference_number"
        file={gatewayFile}
        onFile={onGatewayFile}
        delay={0}
      />
      <FileUploadCard
        label="Bank Statement Export"
        description="transaction_id, amount, date, merchant_name, reference_number"
        file={bankFile}
        onFile={onBankFile}
        delay={1}
      />
    </div>
  )
}
