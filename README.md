# Transaction Reconciliation Tool

A production-quality Python tool for reconciling payment gateway records against bank settlement records, powered by exact matching, fuzzy scoring, and optional LLM (Claude) reasoning.

---

## Project Structure

```
razorpay/
├── reconciler/              # Core package
│   ├── models.py           # Domain types: Transaction, MatchResult, etc.
│   ├── ingest.py           # CSV loading + validation
│   ├── exact_match.py      # reference_number exact matching
│   ├── fuzzy_match.py      # 3-signal fuzzy scoring (date, amount, merchant)
│   ├── llm_reasoning.py    # Claude API integration + fallback
│   ├── pipeline.py         # Orchestrator
│   └── reporting.py        # Metrics, CSVs, Markdown report, JSONL audit trail
│
├── data/
│   ├── generate_data.py    # Synthetic data generator
│   ├── payment_gateway.csv
│   └── bank_settlement.csv
│
├── tests/
│   ├── test_ingest.py
│   ├── test_exact_match.py
│   ├── test_fuzzy_match.py
│   ├── test_pipeline.py
│   └── test_edge_cases.py  # Deliberate failure injection (Prompt 6)
│
├── outputs/                # Created at runtime
├── app.py                  # Streamlit UI
├── requirements.txt
└── .env.example
```

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Generate synthetic test data

```bash
python data/generate_data.py
```

This creates `data/payment_gateway.csv` and `data/bank_settlement.csv` with 80 transactions across 5 scenarios.

### 3. (Optional) Set up Claude API key

```bash
cp .env.example .env
# Edit .env and add your Anthropic API key
```

If no key is set, the tool falls back to rule-based scoring automatically.

### 4. Run the Streamlit UI

```bash
streamlit run app.py
```

Navigate to `http://localhost:8501`.

### 5. Run the tests

```bash
pytest tests/ -v
```

---

## Pipeline Stages

| Stage | Description |
|---|---|
| **Ingest** | Load + validate both CSVs; capture bad rows as `IngestionError` without crashing |
| **Exact Match** | Group by `reference_number`; exact pairs are immediately classified |
| **Fuzzy Candidates** | Score remaining records using date proximity, amount variance %, and rapidfuzz merchant similarity |
| **LLM Reasoning** | Send candidate pairs to Claude with structured prompt; get confidence + reasoning JSON |
| **Classification** | Assign to `matched` / `partial_matches` / `exceptions` based on LLM or rule-based decision |
| **Reporting** | Write CSVs, Markdown report, JSONL audit trail |

---

## Matching Thresholds (defaults)

| Parameter | Default | UI Adjustable |
|---|---|---|
| Date gap | ±3 days | ✅ 1–7 days |
| Amount variance | ±2% | ✅ 0.5–10% |
| Merchant similarity | ≥80% | ✅ 60–100% |
| Min candidate score | 0.50 | No |

---

## Outputs

| File | Description |
|---|---|
| `outputs/matched.csv` | All confirmed matched pairs |
| `outputs/partial_matches.csv` | Fuzzy matches with discrepancy notes |
| `outputs/exceptions.csv` | Records with no match |
| `outputs/exception_report.md` | Human-readable Markdown report |
| `outputs/audit_trail.jsonl` | Full decision log per match, timestamped |

---

## Synthetic Dataset Breakdown

| Group | Count | Description |
|---|---|---|
| Clean matches | 50 | Identical across both files |
| Settlement delay | 10 | Bank date is 1–3 days later |
| Amount variance | 8 | Bank amount ~2% lower (gateway fee) |
| Merchant variants | 5 | Slight misspelling / reformatting |
| True exceptions | 7 | 4 gateway-only + 3 bank-only |

---

## LLM Fallback Behaviour

If the Claude API call fails (network error, invalid key, rate limit), the tool:
1. Retries up to 3 times with exponential backoff
2. Falls back to the rule-based composite score
3. Sets `llm_available = False` in the match result
4. Records `"LLM-unavailable, rule-based only"` in the audit trail

---

## Edge Case Handling (Prompt 6)

The `tests/test_edge_cases.py` suite deliberately injects:

| Edge Case | Behaviour |
|---|---|
| Malformed date | Captured as `IngestionError`, surfaced in exception report |
| Missing/empty amount | Captured as `IngestionError`, pipeline continues on valid rows |
| Non-numeric amount (e.g. "N/A") | Same as above |
| Duplicate `transaction_id` in same file | First row accepted, duplicate captured with reason |
| Both files empty | Returns empty result, no crash |
| Missing required column | Raises `ValueError` immediately with column name |
| Mixed good + bad rows | Good rows match normally; bad rows surface as errors |

---

## Running without LLM

Set `llm_enabled=False` in `ReconciliationConfig` or turn off the toggle in the UI. The pipeline uses only the rule-based composite score:

- Score ≥ 0.85 → `match`
- Score ≥ 0.60 → `partial`
- Score < 0.60 → `exception`
