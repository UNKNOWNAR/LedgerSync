import type { ReconcileConfig, ReconcileResponse } from "./types"

export async function startReconciliation(
  gatewayFile: File,
  bankFile: File,
  config: ReconcileConfig,
): Promise<{ task_id: string }> {
  const form = new FormData()
  form.append("gateway_file", gatewayFile)
  form.append("bank_file", bankFile)
  form.append("config", JSON.stringify(config))

  const res = await fetch("/api/reconcile", {
    method: "POST",
    body: form,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: "Unknown error" }))
    throw new Error(err.error || `HTTP ${res.status}`)
  }

  return res.json()
}

export async function pollTaskStatus(taskId: string): Promise<{ state: string, status: string, result?: ReconcileResponse }> {
  const res = await fetch(`/api/task/${taskId}`)
  if (!res.ok) throw new Error("Failed to fetch task status")
  return res.json()
}

export function getReportUrl(runId: string, reportName: string): string {
  return `/api/reports/${runId}/${reportName}`
}
