"""
LLM-powered reasoning layer for candidate transaction pairs.

For every pair that passes the fuzzy threshold, this module calls the
Claude API to get a structured confidence score and reasoning string.

Fallback behaviour
------------------
If the API call fails after retries, or if config.llm_enabled is False,
the function returns an LLMResult with available=False and the rule-based
composite score as the confidence.  The calling pipeline records
"LLM-unavailable, rule-based only" in the audit trail.

Public API
----------
reason_match(pair, config) -> LLMResult
"""

from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

from .fuzzy_match import CandidatePair
from .models import LLMResult, ReconciliationConfig

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
# ---------------------------------------------------------------------------

_PROMPT_TEMPLATE = """\
You are an expert financial reconciliation analyst. Your task is to evaluate \
whether two transaction records from different systems represent the same \
underlying payment.

## Gateway Transaction
- Transaction ID : {gw_id}
- Amount         : ₹{gw_amount:.2f}
- Date           : {gw_date}
- Merchant       : {gw_merchant}
- Reference No.  : {gw_ref}

## Bank Settlement Record
- Transaction ID : {bank_id}
- Amount         : ₹{bank_amount:.2f}
- Date           : {bank_date}
- Merchant       : {bank_merchant}
- Reference No.  : {bank_ref}

## Discrepancy Notes (from rule-based analysis)
{notes}

## Your Task
Analyse both records carefully. Consider:
1. Whether the amount difference is consistent with a gateway processing fee.
2. Whether the date gap is consistent with typical T+1 to T+3 bank settlement cycles.
3. Whether the merchant names refer to the same entity despite formatting differences.

Respond with ONLY a valid JSON object in this exact format:
{{
  "confidence": <float between 0.0 and 1.0>,
  "decision": "<match|partial|exception>",
  "reasoning": "<one to three concise sentences explaining your conclusion>"
}}

Where:
- "match"     = same transaction, minor/expected discrepancies
- "partial"   = probably same transaction but significant discrepancy warrants review
- "exception" = likely NOT the same transaction
"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def reason_match(
    pair: CandidatePair,
    config: ReconciliationConfig,
) -> LLMResult:
    """
    Call the Claude API to reason about a fuzzy candidate pair.

    Returns an LLMResult.  On any failure, returns a fallback result with
    available=False and the rule-based composite score.
    """
    if not config.llm_enabled:
        return _fallback(pair, reason="LLM disabled by configuration")

    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        return _fallback(pair, reason="GROQ_API_KEY not set")

    prompt = _build_prompt(pair)

    last_error: Optional[Exception] = None
    for attempt in range(1, config.llm_max_retries + 1):
        try:
            result = _call_api(prompt, api_key, config.llm_model)
            logger.info(
                "LLM reasoning succeeded (attempt %d): decision=%s, confidence=%.2f",
                attempt,
                result.decision,
                result.confidence,
            )
            return result
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            logger.warning(
                "LLM call attempt %d/%d failed: %s",
                attempt,
                config.llm_max_retries,
                exc,
            )
            if attempt < config.llm_max_retries:
                time.sleep(2 ** attempt)   # exponential back-off

    return _fallback(
        pair,
        reason=f"LLM-unavailable after {config.llm_max_retries} retries: {last_error}",
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _build_prompt(pair: CandidatePair) -> str:
    gw = pair.gateway_tx
    bank = pair.bank_tx
    notes_str = (
        "\n".join(f"- {n}" for n in pair.discrepancy_notes)
        if pair.discrepancy_notes
        else "- None (amounts / dates / names appear identical)"
    )
    return _PROMPT_TEMPLATE.format(
        gw_id=gw.transaction_id,
        gw_amount=gw.amount,
        gw_date=gw.date,
        gw_merchant=gw.merchant_name,
        gw_ref=gw.reference_number,
        bank_id=bank.transaction_id,
        bank_amount=bank.amount,
        bank_date=bank.date,
        bank_merchant=bank.merchant_name,
        bank_ref=bank.reference_number,
        notes=notes_str,
    )


def _call_api(prompt: str, api_key: str, model: str) -> LLMResult:
    """Make the actual Groq API call and parse the JSON response."""
    try:
        import groq  # imported lazily to avoid hard dep at import time
    except ImportError as exc:
        raise RuntimeError(
            "groq package not installed. Run: pip install groq"
        ) from exc

    client = groq.Groq(api_key=api_key)
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system", 
                "content": "You are a financial reconciliation API. You must output ONLY raw JSON."
            },
            {
                "role": "user", 
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=512,
        response_format={"type": "json_object"}
    )

    raw = completion.choices[0].message.content.strip()
    parsed = _parse_llm_response(raw)

    return LLMResult(
        available=True,
        confidence=float(parsed.get("confidence", 0.5)),
        decision=str(parsed.get("decision", "partial")),
        reasoning=str(parsed.get("reasoning", "")),
        raw_response=raw,
    )


def _parse_llm_response(raw: str) -> dict:
    """Extract JSON from the LLM response, tolerating minor wrapping."""
    # Strip markdown code fences if present
    text = raw
    if "```" in text:
        start = text.find("{")
        end = text.rfind("}") + 1
        text = text[start:end]
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Attempt to extract just the JSON object
        import re
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            data = json.loads(match.group())
        else:
            raise ValueError(f"Could not parse JSON from LLM response: {raw!r}")
    return data


def _fallback(pair: CandidatePair, reason: str) -> LLMResult:
    """Build a fallback LLMResult when the API is unavailable."""
    logger.info("Using rule-based fallback: %s", reason)
    return LLMResult(
        available=False,
        confidence=pair.composite_score,
        decision=_rule_based_decision(pair.composite_score),
        reasoning=f"LLM-unavailable, rule-based only. {reason}",
        raw_response=None,
    )


def _rule_based_decision(score: float) -> str:
    if score >= 0.85:
        return "match"
    if score >= 0.60:
        return "partial"
    return "exception"
