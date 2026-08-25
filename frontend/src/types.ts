export interface Transaction {
  transaction_id: string
  amount: number
  date: string
  merchant_name: string
  reference_number: string
  source: string
}

export interface MatchResult {
  gateway_tx: Transaction | null
  bank_tx: Transaction | null
  status: 'exact' | 'fuzzy_llm' | 'fuzzy_rule' | 'exception'
  confidence: number
  rule_score: number
  discrepancy_notes: string[]
  llm_reasoning: string
  llm_available: boolean
  matched_at: string | null
}

export interface IngestionError {
  source: string
  row_index: number
  raw_data: Record<string, unknown>
  reason: string
}

export interface Metrics {
  total_gateway_records: number
  total_bank_records: number
  total_records: number
  matched_count: number
  match_rate_pct: number
  exact_matches: number
  fuzzy_llm_matches: number
  fuzzy_rule_matches: number
  partial_matches: number
  exceptions: number
  ingestion_errors: number
}

export interface ReconcileResponse {
  run_id: string
  metrics: Metrics
  matched: MatchResult[]
  partial_matches: MatchResult[]
  exceptions: MatchResult[]
  ingestion_errors: IngestionError[]
}

export interface ReconcileConfig {
  date_gap_days: number
  amount_variance_pct: number
  merchant_similarity_threshold: number
  llm_enabled: boolean
}
