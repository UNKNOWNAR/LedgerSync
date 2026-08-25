import type { ReconcileConfig, ReconcileResponse } from './types'

export async function reconcile(
  gatewayFile: File,
  bankFile: File,
  config: ReconcileConfig,
): Promise<ReconcileResponse> {
  const form = new FormData()
  form.append('gateway_file', gatewayFile)
  form.append('bank_file', bankFile)
  form.append('config', JSON.stringify(config))

  const res = await fetch('/api/reconcile', {
    method: 'POST',
    body: form,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'Unknown error' }))
    throw new Error(err.error || `HTTP ${res.status}`)
  }

  return res.json()
}

export function getReportUrl(runId: string, reportName: string): string {
  return `/api/reports/${runId}/${reportName}`
}
