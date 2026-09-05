# Transaction Reconciliation — Exception Report

_Generated: 2026-09-05 16:20:44_

## Summary Metrics

| Metric | Value |
|---|---|
| Total Gateway Records | 77 |
| Total Bank Records | 76 |
| Matched (Exact) | 73 |
| Matched (Fuzzy LLM) | 0 |
| Matched (Fuzzy Rule) | 0 |
| Partial Matches | 0 |
| Exceptions | 7 |
| Ingestion Errors | 0 |
| **Match Rate** | **94.81%** |

## Exceptions (No Match Found)

### 1. Exception — Gateway TX `GW00077`

| Field | Value |
|---|---|
| transaction_id | GW00077 |
| amount | ₹330.12 |
| date | 2026-02-14 |
| merchant_name | IRCTC Rail |
| reference_number | PAY727065173961 |
| source | gateway |

**Reason:**
- No matching record found in bank file.

### 2. Exception — Gateway TX `GW00076`

| Field | Value |
|---|---|
| transaction_id | GW00076 |
| amount | ₹5715.14 |
| date | 2026-04-12 |
| merchant_name | Goibibo Hotels |
| reference_number | NEFT741038689082 |
| source | gateway |

**Reason:**
- No matching record found in bank file.

### 3. Exception — Gateway TX `GW00075`

| Field | Value |
|---|---|
| transaction_id | GW00075 |
| amount | ₹33030.37 |
| date | 2026-05-27 |
| merchant_name | BookMyShow |
| reference_number | NEFT713758808009 |
| source | gateway |

**Reason:**
- No matching record found in bank file.

### 4. Exception — Gateway TX `GW00074`

| Field | Value |
|---|---|
| transaction_id | GW00074 |
| amount | ₹394.98 |
| date | 2026-01-02 |
| merchant_name | Policy Bazaar |
| reference_number | PAY426460350321 |
| source | gateway |

**Reason:**
- No matching record found in bank file.

### 5. Exception — Bank TX `BK00079`

| Field | Value |
|---|---|
| transaction_id | BK00079 |
| amount | ₹13611.86 |
| date | 2026-06-02 |
| merchant_name | Kalyan Jewellers |
| reference_number | TXN446753040326 |
| source | bank |

**Reason:**
- No matching record found in gateway file.

### 6. Exception — Bank TX `BK00080`

| Field | Value |
|---|---|
| transaction_id | BK00080 |
| amount | ₹8535.56 |
| date | 2026-07-02 |
| merchant_name | PVR Cinemas |
| reference_number | IMPS359709516594 |
| source | bank |

**Reason:**
- No matching record found in gateway file.

### 7. Exception — Bank TX `BK00078`

| Field | Value |
|---|---|
| transaction_id | BK00078 |
| amount | ₹972.90 |
| date | 2026-03-22 |
| merchant_name | Manyavar |
| reference_number | IMPS170964556869 |
| source | bank |

**Reason:**
- No matching record found in gateway file.
